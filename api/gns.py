import queue
import socket

from api.gnscontext import GNSContext, SendingHUDPPacket, RecvingHUDPPacket
from api.states.gnssclosewait import GNSStateCloseWait
from api.states.gnssfinwait1 import GNSStateFinWait1
from api.states.gnssinitial import GNSStateInitial
from api.states.gnssbound import GNSStateBound
from api.states.gnsslastack import GNSStateLastAck
from api.states.gnsslisten import GNSStateListen
from api.states.gnssaccept import GNSStateAccept
from api.states.gnsssynsent import GNSStateSynSent
from api.states.gnsstate import GNSState
from api.states.gnssterminated import GNSStateTerminated
from common import AddrPort, IllegalStateChangeException, CLIENT_PORT
from hudp import HUDPPacket
from threading import Thread
import time


class GameNetSocket:
    """
    Socket-like API for the GameNet protocol.
    The way to use it is really similar to using a TCP socket.
    Behaviours are heavily influenced by RFC9293: Transmission Control Protocol.

    The socket is implemented like a Finite State Machine. Throughout the lifetime of the
    socket, its state will change depending on user interactions and responses from remote connection.

    This socket represents a 1-to-1 connection between two hosts.
    """

    def __init__(self):
        self.context = GNSContext()
        """
        Information to be kept track of and share across all states.
        """

        self.state: GNSState = GNSStateInitial()
        """
        Current state of the socket.
        """

    def bind(self, addrPort: AddrPort):
        """
        Bind this socket to a specific address and port number.
        """
        if not isinstance(self.state, GNSStateInitial):
            raise IllegalStateChangeException("Can only bind() an INITIAL socket")
        self.context.sendAddrPort = addrPort
        self.context.sock.bind(addrPort)
        self.__transition(GNSStateBound())

    def listen(self):
        """
        Begin listening on connection requests. The socket must be bound before this.
        """
        if not isinstance(self.state, GNSStateBound):
            raise IllegalStateChangeException("Can only listen() on a BOUND socket")
        # Start the thread to receive packets from remotes
        Thread(target=self.__recv).start()
        self.__transition(GNSStateListen())

    def accept(self):
        """
        Begin accepting the connection requests. The socket must be listened on before this.
        Return after connection with a remote is established.
        """
        if not isinstance(self.state, GNSStateListen):
            raise IllegalStateChangeException("Can only accept() on a LISTEN socket")
        self.__transition(GNSStateAccept())
        # Start the thread to process incoming and outgoing packets.
        Thread(target=self.__routine).start()
        # Start the thread to send packets to remote.
        Thread(target=self.__send).start()
        self.context.acceptSemaphore.acquire()
        return

    def connect(self, addrPort: AddrPort):
        """
        Attempts to connect to an address and port number.
        The socket must not be used in any ways before this.
        Return after connection with a remote is established.
        """
        if not (isinstance(self.state, GNSStateInitial) or isinstance(self.state, GNSStateBound)):
            raise IllegalStateChangeException("Can only connect() on a INITIAL socket")

        # Bind the socket to a specific address and port number.
        # This is the only difference from TCP.
        if isinstance(self.state, GNSStateInitial):
            self.bind(('127.0.0.1', CLIENT_PORT))

        # Send the first SYN packet to initiate the 3-way handshake.
        self.context.destAddrPort = addrPort
        syn = HUDPPacket.create(self.context.seq, 0, isReliable=True, isSyn=True)
        self.context.seq += 1
        self.context.sendWindow.put(SendingHUDPPacket(syn))

        # Transition to a transient state
        self.context.stateSemaphore.acquire()
        self.__transition(GNSStateSynSent())
        self.context.stateSemaphore.release()

        # Start all threads to manage operations of the socket
        Thread(target=self.__recv).start()
        Thread(target=self.__routine).start()
        Thread(target=self.__send).start()

        self.context.connectSemaphore.acquire()

    def send(self, data: bytes, isReliable: bool):
        """
        Send data to remote. A connection must be established before this.
        :param data: Information to be sent to remote.
        :param isReliable: True if Reliable channel is to be used. False otherwise.
        :return:
        """
        packet = HUDPPacket.create(self.context.seq, self.context.ack, data, isReliable=isReliable, isAck=isReliable)
        # Only increment sequence number if packet is reliable
        if not packet.isUnreliable():
            self.context.seq += len(data)
        self.context.sendWindow.put(SendingHUDPPacket(packet))

    def recv(self) -> bytes:
        """
        Return data sent from remote. This function will block until there is data to receive.
        A connection must be established before this.
        """
        data = self.context.recvBuffer.get()
        return data

    def close(self):
        """
        Close the connection. A connection must be established before this.
        """
        fin = HUDPPacket.create(self.context.seq, self.context.ack, isReliable=True, isFin=True)
        self.context.seq += 1
        self.context.sendWindow.put(SendingHUDPPacket(fin))

        # Semaphore is needed to prevent race-conditions from multiple threads trying to change states.
        self.context.stateSemaphore.acquire()
        if isinstance(self.state, GNSStateCloseWait):
            self.__transition(GNSStateLastAck())
        else:
            self.__transition(GNSStateFinWait1())
        self.context.stateSemaphore.release()
        self.context.closeSemaphore.acquire()
        return

    def __transition(self, newState: GNSState):
        """
        Transition the socket's state to a new one.
        :param newState: The new state to be changed to.
        """
        print(type(newState))
        self.state = newState

    def __routine(self):
        """
        Retrieves incoming and outgoing packets and process them accordingly.
        This function is executed once every 10 milliseconds to ensure low latency.
        """
        while True:
            # If state becomes TERMINATED, terminates this thread
            if isinstance(self.state, GNSStateTerminated):
                break

            # Repeatedly process packets until the state does not change anymore
            self.context.stateSemaphore.acquire()
            newState = self.state.process(self.context)
            while type(self.state) is not type(newState):
                self.__transition(newState)
                newState = self.state.process(self.context)
            self.context.stateSemaphore.release()

            # Send back Pure ACK if needed
            if self.context.shouldSendAck:
                self.context.shouldSendAck = False
                self.context.sendWindow.put(
                    SendingHUDPPacket(HUDPPacket.createPureAck(self.context.seq, self.context.ack)))

            # Put timed-out packets into 'sendWindow'
            currentTime = time.time()
            while self.context.sendBuffer.qsize() > 0:
                sendingPacket = self.context.sendBuffer.get()
                # If the sequence number of this packet has already been acknowledged by
                # remote, there is no need to transmit it.
                if sendingPacket.packet.seq < self.context.rec:
                    continue
                # Only transmit packets that are ready.
                if sendingPacket.retryAt >= currentTime:
                    self.context.sendBuffer.put(sendingPacket)
                    # If this packet is not ready, all packets after it are also not ready
                    # due to the ordering of the PriorityQueue
                    break
                self.context.sendWindow.put(sendingPacket)

            time.sleep(0.010)

    def __send(self):
        """
        Sends all packets in 'sendWindow'. This function is executed in its own thread.
        """
        while True:
            # If state becomes TERMINATED, terminates this thread
            if isinstance(self.state, GNSStateTerminated):
                break
            try:
                sendingPacket = self.context.sendWindow.get(timeout=0.200)
                packetBytes = sendingPacket.packet.toBytes()
                if self.context.destAddrPort:
                    self.context.sock.sendto(packetBytes, self.context.destAddrPort)
                else:
                    raise RuntimeError("This branch is not supposed to be matched")
                sendingPacket.decrementRetry()
                # If there are still retries left, put it back into the buffer
                if sendingPacket.retryLeft > 0:
                    self.context.sendBuffer.put(sendingPacket)
            except queue.Empty as e:
                continue

    def __recv(self):
        """
        Receives packets in from socket. This function is executed in its own thread.
        """
        while True:
            # If state becomes TERMINATED, terminates this thread
            if isinstance(self.state, GNSStateTerminated):
                break
            try:
                data, addrPort = self.context.sock.recvfrom(16384)
                # Ensure packets pass checksum
                if HUDPPacket.verifyChecksum(data):
                    # If connection is established and address does not match, drop it
                    if self.context.destAddrPort is not None and addrPort != self.context.destAddrPort:
                        continue
                    packet = HUDPPacket.fromBytes(data)
                    self.context.shouldSendAck = self.context.shouldSendAck or packet.isDataPacket()
                    self.context.recvWindow.put(RecvingHUDPPacket(HUDPPacket.fromBytes(data), addrPort))
            except socket.timeout as e:
                continue
