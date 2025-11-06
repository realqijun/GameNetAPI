from __future__ import annotations
from threading import Semaphore
from hudp import HUDPPacket
from queue import Queue, PriorityQueue
from common import AddrPort, MAX_RETRY, RETRY_INCREMENT, MAX_SEND_WINDOW_SIZE
import socket
import time


class SendingHUDPPacket:
    """
    Represent a HUDP packet that is about to be sent.
    """

    def __init__(self, packet: HUDPPacket):
        self.packet = packet
        """
        The HUDP packet itself.
        """

        self.retryLeft = 1 if packet.isUnreliable() else MAX_RETRY
        """
        Number of retries remaining for this packet. Initially 1 for unreliable packets and 15 for reliable ones.
        """

        self.retryAt = time.time()

    def decrementRetry(self):
        """
        Decrement the number of retries remaining and set a new time for this packet to be re-sent.
        """

        self.retryLeft -= 1
        self.retryAt += RETRY_INCREMENT

    def __lt__(self, other: SendingHUDPPacket):
        """
        Provide the ordering for the PriorityQueue.
        """
        return self.retryAt < other.retryAt


class RecvingHUDPPacket:
    """
    Represent a HUDP packet that is about to be processed.
    """

    def __init__(self, packet: HUDPPacket, addrPort: AddrPort):
        self.packet = packet
        """
        The HUDP packet itself.
        """

        self.addrPort = addrPort
        """
        Address and port number from where this packet was sent.
        """

        self.arrivalTime = time.time()
        """
        Arrival time of this packet
        """

    def __lt__(self, other: RecvingHUDPPacket):
        """
        Provide the ordering for the PriorityQueue.
        """
        return self.arrivalTime < other.arrivalTime


class GNSContext:
    """
    Wrapper class for all information to be kept tracked of for the HUDP reliable delivery service.
    """

    def __init__(self):
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        """
        The underlying UDP packet. Timeout time is 0.200 seconds.
        """
        self.sock.settimeout(0.200)

        self.seq: int = 0
        """
        Sequence Number of the next packet to be sent. Initially random to simulate actual TCP behaviour.
        """

        self.rec: int = 0
        """
        Largest received Acknowledgement Number from remote.
        """

        self.ack: int = 0
        """
        Next expected Sequence Number to be received from remote.
        """

        self.sendWindow: Queue[SendingHUDPPacket] = Queue(maxsize=MAX_SEND_WINDOW_SIZE)
        """
        Queue to store ready-to-send packets. Timeout is 0.200s.
        GameNetSocket will create a thread to continually retrieves packets from this queue and send it.
        """

        self.sendBuffer: PriorityQueue[SendingHUDPPacket] = PriorityQueue()
        """
        PriorityQueue to store packets that are not ready to be sent, i.e. waiting for timeout.
        The Queue is ordered from closest to furthest away from timing out (e.g. a packet
        that times out in 100ms is in front of a packet that times out in 200ms).
        GameNetSocket has a routine to check when packets times out and put them into 'sendWindow'.
        """

        self.recvWindow: Queue[RecvingHUDPPacket] = Queue()
        """
        PriorityQueue to store about-to-be-processed packets.
        The Queue is ordered from packets with lowest to highest sequence numbers (e.g. a packet with
        a sequence number of 100 will be in front of a packet with sequence number of 200).
        GameNetSocket will create a thread to continually retrieves packets from the UDP socket and place it here.
        Provides the buffering needed for packet reordering.
        """

        self.recvBuffer: Queue[bytes] = Queue()
        """
        Queue to store packets' data that are ready to be received by the client.
        """

        self.sendAddrPort: AddrPort = None
        """
        Address and port number of the UDP socket.
        """
        self.destAddrPort: AddrPort = None
        """
        Address and port number of remote.
        """

        self.shouldSendAck: bool = False
        """
        Whether a data packet was received. This is for deciding transmission of ACK packets, especially
        if the data packet received was out-of-order.
        """

        self.acceptSemaphore: Semaphore = Semaphore(0)
        """
        Semaphore to block accept() function from returning until the 3-way handshake is complete.
        """

        self.connectSemaphore: Semaphore = Semaphore(0)
        """
        Semaphore to block connect() function from returning until the 3-way handshake is complete.
        """

        self.closeSemaphore: Semaphore = Semaphore(0)
        """
        Semaphore to block close() function from returning until the FIN packet sent is acknowledged by remote.
        """

        self.stateSemaphore: Semaphore = Semaphore(1)
        """
        Semaphore to safely update socket state.
        """
