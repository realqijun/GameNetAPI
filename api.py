from collections import deque
from hudp import HUDPPacket
from queue import Queue
from threading import Thread, Lock
from typing import Deque
import socket
import time

TIMEOUT = 0.200
MAX_BUFFER_LEN = 1024
MAX_WINDOW_LEN = 64


class SendingHUDPPacket:
    def __init__(self, packet: HUDPPacket, retryLeft: int, timeSent: float):
        self.packet = packet
        self.retryLeft = retryLeft
        self.timeSent = timeSent


class GameNetAPI:
    def __init__(self):
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq: int = 0
        self.rec: int = 0
        self.ack: int = 0
        self.sendAckNext: bool = False
        self.waitingSeq: int = -1
        self.timeSinceWaitingSeq: float = -1
        self.sendBufferLock: Lock = Lock()
        self.sendBuffer: Deque[HUDPPacket] = deque(maxlen=MAX_BUFFER_LEN)
        self.sendWindow: Deque[SendingHUDPPacket] = deque(maxlen=MAX_WINDOW_LEN)
        self.recvBuffer: Queue[bytes] = Queue(maxsize=MAX_BUFFER_LEN)
        self.recvWindowLock: Lock = Lock()
        self.recvWindow: Deque[HUDPPacket] = deque(maxlen=MAX_WINDOW_LEN)
        routine = Thread(target=self.__routine)
        routine.start()

    def bind(self, ipAddress: str, port: int):
        self.sock.bind((ipAddress, port))

    def listen(self):
        receiver = Thread(target=self.__recv)
        receiver.start()

    def send(self, data: bytes, isReliable: bool):
        packet = HUDPPacket.create(self.seq, self.ack, data, isReliable, isAck=True)
        self.seq += len(data)
        with self.sendBufferLock:
            self.sendBuffer.append(packet)

    def recv(self) -> bytes:
        data = self.recvBuffer.get(block=True)
        return data

    def __recv(self):
        while True:
            data, _ = self.sock.recvfrom(16384)
            if not HUDPPacket.verifyChecksum(data):
                continue
            with self.recvWindowLock:
                self.recvWindow.append(HUDPPacket.fromBytes(data))

    def __processRecvPacket(self, packet: HUDPPacket) -> bool:
        if packet.flags.isSyn and not packet.flags.isAck:
            self.ack = packet.seq + 1
            reply = HUDPPacket.create(self.seq, self.ack, bytes(), isReliable=True, isSyn=True, isAck=True)
            with self.sendBufferLock:
                self.sendBuffer.append(reply)
            return True
        elif packet.flags.isSyn and packet.flags.isAck:
            self.ack = packet.seq + 1
            reply = HUDPPacket.create(self.seq, self.ack, bytes(), isReliable=True, isAck=True)
            with self.sendBufferLock:
                self.sendBuffer.append(reply)
            return True
        else:
            if len(packet.content) == 0 and packet.flags.isAck:
                self.rec = max(self.rec, packet.ack)
                return True

            if len(packet.content) > 0 and packet.seq < self.ack:
                self.sendAckNext = True
                return True

            if len(packet.content) > 0 and packet.seq == self.ack:
                self.ack = packet.seq + len(packet.content)
                self.recvBuffer.put(packet.content)
                self.sendAckNext = True
                return True

            if packet.seq == self.waitingSeq and time.time() - self.timeSinceWaitingSeq > TIMEOUT * 5:
                self.ack = packet.seq + len(packet.content)
                self.recvBuffer.put(packet.content)
                self.sendAckNext = True
                self.waitingSeq = -1
                self.timeSinceWaitingSeq = -1
                return True

            if packet.seq > self.ack:
                self.timeSinceWaitingSeq = time.time()
                self.waitingSeq = packet.seq
                return False

            return False

    def __routine(self):
        while True:
            with self.recvWindowLock:
                recvSorted = sorted(self.recvWindow, key=lambda packet: packet.seq)
                self.recvWindow.clear()
                self.recvWindow.extend(recvSorted)
                while len(self.recvWindow) > 0:
                    status = self.__processRecvPacket(self.recvWindow[0])
                    if status:
                        self.recvWindow.popleft()
                    else:
                        break

            filtered = [sending for sending in self.sendWindow if sending.packet.seq >= self.rec]
            self.sendWindow.clear()
            self.sendWindow.extend(filtered)

            with self.sendBufferLock:
                while len(self.sendWindow) < MAX_WINDOW_LEN and len(self.sendBuffer) > 0:
                    self.sendWindow.append(SendingHUDPPacket(self.sendBuffer.popleft(), 5, 0))

            if self.sendAckNext:
                self.sock.sendto(HUDPPacket.create(self.seq, self.ack, bytes(), isReliable=True, isAck=True).toBytes(), ('127.0.0.1', 55000))
                self.sendAckNext = False

            currentTime = time.time()
            for sending in self.sendWindow:
                if currentTime - sending.timeSent > TIMEOUT:
                    self.sock.sendto(sending.packet.toBytes(), ('127.0.0.1', 55000))
                    sending.timeSent = time.time()
                    sending.retryLeft -= 1

            filtered = [sending for sending in self.sendWindow if sending.retryLeft > 0]
            self.sendWindow.clear()
            self.sendWindow.extend(filtered)

            time.sleep(0.010)

    def connect(self, ipAddress: str, port: int) -> bool:
        addr = (ipAddress, port)

        def isSynAckPacket(data: bytes) -> bool:
            if not HUDPPacket.verifyChecksum(data):
                return False
            synAckPacket = HUDPPacket.fromBytes(data)
            if not (synAckPacket.flags.isSyn and synAckPacket.flags.isAck):
                return False
            return True

        # First packet in the 3-way handshake
        synPacket = HUDPPacket.create(0, 0, bytes(), isReliable=True, isSyn=True)
        isConnected = False
        retryLeft = 5
        while retryLeft > 0:
            try:
                self.sock.sendto(synPacket.toBytes(), addr)
                synAckBytes, _ = self.sock.recvfrom(16384)
                if not isSynAckPacket(synAckBytes):
                    print(HUDPPacket.checksum1s(synAckBytes))
                    retryLeft -= 1
                    continue

                isConnected = True
                break
            except socket.timeout:
                retryLeft -= 1

        if not isConnected:
            return False

        # Third packet in the 3-way handshake
        ackPacket = HUDPPacket.create(0, 0, bytes(), isReliable=True, isAck=True)
        self.sock.sendto(ackPacket.toBytes(), addr)

        # Make sure server really receives the last ACK packet
        start = time.time()
        while time.time() - start < TIMEOUT * 5:
            try:
                synAckBytes, _ = self.sock.recvfrom(16384)
                if not isSynAckPacket(synAckBytes):
                    # NOTE: This may be a valid packet from the server but it is ok to disard this packet here.
                    # The server will resend it again after not receiving the ACK.
                    continue
                else:
                    self.sock.sendto(ackPacket.toBytes(), addr)
                    start = time.time()
            except socket.timeout:
                continue

        return True

    def accept(self):
        while True:
            def isSynPacket(data: bytes):
                if not HUDPPacket.verifyChecksum(data):
                    return False
                synAckPacket = HUDPPacket.fromBytes(data)
                if not synAckPacket.flags.isSyn:
                    return False
                return True

            def isAckPacket(data: bytes):
                if not HUDPPacket.verifyChecksum(data):
                    return False
                ackPacket = HUDPPacket.fromBytes(data)
                if not ackPacket.flags.isAck:
                    return False
                return True

            try:
                synBytes, addr = self.sock.recvfrom(16384)
                if not isSynPacket(synBytes):
                    continue

                synAckPacket = HUDPPacket.create(0, 0, bytes(), isReliable=True, isSyn=True, isAck=True)
                self.sock.sendto(synAckPacket.toBytes(), addr)

                # Make sure client really receives the SYN ACK packet
                retryLeft = 5
                while retryLeft > 0:
                    try:
                        ackBytes, _ = self.sock.recvfrom(16384)
                        if isAckPacket(ackBytes):
                            break
                    except socket.timeout:
                        self.sock.sendto(synAckPacket.toBytes(), addr)
                        retryLeft -= 1
            except socket.timeout:
                continue
