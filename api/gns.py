from gnscontext import GNSContext, SendingHUDPPacket
from states.gnssclosed import GNSStateClosed
from states.gnsslisten import GNSStateListen
from states.gnsstate import GNSState
from common import IllegalOperationException, AddrPort
from protocol.hudp import HUDPPacket
from threading import Thread, Lock, Semaphore
import time


class GameNetSocket:
    def __init__(self):
        self.state: GNSState = GNSStateClosed()
        self.stateSemaphore: Semaphore = Semaphore(2)
        self.context = GNSContext()

    def bind(self, addrPort: AddrPort):
        self.ensureNotBinded()
        self.ensureNotConnected()
        self.context.bindAddrPort = addrPort
        self.context.sock.bind(addrPort)

    def listen(self):
        self.ensureBinded()
        self.ensureNotConnected()
        self.__transition(GNSStateListen())
        recvRoutine = Thread(target=self.__recv)
        recvRoutine.start()

    def accept(self):
        self.ensureBinded()
        self.ensureNotConnected()
        routine = Thread(target=self.__routine)
        routine.start()
        sendRoutine = Thread(target=self.__send)
        sendRoutine.start()
        # Block until acceptQueue get filled from __routine
        self.context.destAddrPort = self.context.acceptQueue.get()

    def connect(self, addrPort: AddrPort):
        self.ensureNotConnected()
        # TODO: Accepting here

    def send(self, data: bytes, isReliable: bool):
        self.ensureConnected()
        packet = HUDPPacket.create(self.context.seq, self.context.ack, data, isReliable=isReliable)
        if isReliable:
            packet.flags.isAck = True
        self.context.seq += len(data)
        self.context.sendBuffer.put(SendingHUDPPacket(packet))

    def recv(self) -> bytes:
        self.ensureConnected()
        data = self.context.clientRecvBuffer.get()
        return data

    def close(self):
        self.ensureConnected()
        # TODO: Transition to closing here

    def __routine(self):
        while True:
            self.stateSemaphore.acquire()
            newState = self.state.__routine(self.context)
            self.stateSemaphore.release()
            self.__transition(newState)
            time.sleep(0.010)

    def __send(self):
        while True:
            sendingPacket = self.context.sendWindow.get()
            packetBytes = sendingPacket.packet.toBytes()
            if self.context.destAddrPort:
                self.context.sock.sendto(packetBytes, self.context.destAddrPort)
            elif self.context.tempDestAddrPort:
                self.context.sock.sendto(packetBytes, self.context.tempDestAddrPort)
            else:
                raise RuntimeError("This branch is not supposed to be matched")
            sendingPacket.decrementRetry()
            if sendingPacket.retryLeft > 0:
                self.context.sendBuffer.put(sendingPacket)

    def __recv(self):
        while True:
            data, addrPort = self.context.sock.recvfrom(16384)
            if HUDPPacket.verifyChecksum(data):
                self.stateSemaphore.acquire()
                self.state.__recv(self.context, data, addrPort)
                self.stateSemaphore.release()

    def __transition(self, newState: GNSState):
        self.stateSemaphore.acquire()
        self.stateSemaphore.acquire()
        self.state = newState
        self.stateSemaphore.release()
        self.stateSemaphore.release()

    def ensureNotBinded(self):
        if self.context.bindAddrPort is not None:
            raise IllegalOperationException("Socket has already been binded")

    def ensureBinded(self):
        if self.context.bindAddrPort is None:
            raise IllegalOperationException("Socket has not been binded")

    def ensureNotConnected(self):
        if self.context.bindAddrPort is not None:
            raise IllegalOperationException("Socket is already connected")

    def ensureConnected(self):
        if self.context.bindAddrPort is None:
            raise IllegalOperationException("Socket has not been connected")
