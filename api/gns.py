from api.gnscontext import GNSContext, SendingHUDPPacket, RecvingHUDPPacket
from api.states.gnssinitial import GNSStateInitial
from api.states.gnssbinded import GNSStateBinded
from api.states.gnsslisten import GNSStateListen
from api.states.gnssaccept import GNSStateAccept
from api.states.gnsssynsent import GNSStateSynSent
from api.states.gnsstate import GNSState
from common import AddrPort, IllegalStateChangeException, CLIENT_PORT
from hudp import HUDPPacket
from threading import Thread
import time


class GameNetSocket:
    def __init__(self):
        self.state: GNSState = GNSStateInitial()
        self.context = GNSContext()

    def bind(self, addrPort: AddrPort):
        if not isinstance(self.state, GNSStateInitial):
            raise IllegalStateChangeException("Can only bind() an INITIAL socket")
        self.context.bindAddrPort = addrPort  # TODO: change this to sendAddrPort for more universal usage
        self.context.sock.bind(addrPort)
        self.state = GNSStateBinded()

    def listen(self):
        if not isinstance(self.state, GNSStateBinded):
            raise IllegalStateChangeException("Can only listen() on a BINDED socket")
        Thread(target=self.__recv).start()
        self.state = GNSStateListen()

    def accept(self):
        if not isinstance(self.state, GNSStateListen):
            raise IllegalStateChangeException("Can only accept() on a LISTEN socket")
        self.state = GNSStateAccept()
        Thread(target=self.__routine).start()
        Thread(target=self.__send).start()
        self.context.acceptSemaphore.acquire()
        return

    def connect(self, addrPort: AddrPort):
        if not (isinstance(self.state, GNSStateInitial) or isinstance(self.state, GNSStateBinded)):
            raise IllegalStateChangeException("Can only connect() on a INITIAL socket")

        if isinstance(self.state, GNSStateInitial):
            self.bind(('127.0.0.1', CLIENT_PORT))

        self.context.destAddrPort = addrPort
        syn = HUDPPacket.create(self.context.seq, 0, bytes(), isReliable=True, isSyn=True)
        self.context.seq += 1
        self.context.sendWindow.put(SendingHUDPPacket(syn))
        self.state = GNSStateSynSent()
        Thread(target=self.__recv).start()
        Thread(target=self.__routine).start()
        Thread(target=self.__send).start()

    def send(self, data: bytes, isReliable: bool):
        packet = HUDPPacket.create(self.context.seq, self.context.ack, data, isReliable=isReliable)
        if isReliable:
            packet.flags.isAck = True
        self.context.seq += len(data)
        self.context.sendBuffer.put(SendingHUDPPacket(packet))

    def recv(self) -> bytes:
        data = self.context.clientRecvBuffer.get()
        return data

    def close(self):
        pass
        # TODO: Transition to closing here

    def __routine(self):
        while True:
            newState = self.state.process(self.context)
            self.state = newState
            currentTime = time.time()
            while self.context.sendBuffer.qsize() > 0:
                sendingPacket = self.context.sendBuffer.get()
                if sendingPacket.packet.seq < self.context.rec:
                    continue
                if sendingPacket.retryAt >= currentTime:
                    self.context.sendBuffer.put(sendingPacket)
                    break
                self.context.sendWindow.put(sendingPacket)
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
                self.context.recvWindow.put(RecvingHUDPPacket(HUDPPacket.fromBytes(data), addrPort))
