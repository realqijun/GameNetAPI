from hudp import HUDPPacket
import socket
import time

TIMEOUT = 0.200


class GameNetAPI:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(TIMEOUT)

    def bind(self, ipAddress: str, port: int):
        self.sock.bind((ipAddress, port))

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

    def send(data: bytes, isReliable: bool):
        i = 0

    def recv() -> bytes:
        i = 0
