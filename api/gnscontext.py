from __future__ import annotations
from threading import Semaphore
from hudp import HUDPPacket
from queue import Queue, PriorityQueue
from common import AddrPort
import socket
import time

MAX_WINDOW_SIZE = 4096
MAX_BUFFER_SIZE = 4096


class SendingHUDPPacket:
    def __init__(self, packet: HUDPPacket):
        self.packet = packet
        self.retryLeft = 1 if packet.isUnreliable() else 15
        self.retryAt = time.time()

    def decrementRetry(self):
        self.retryLeft -= 1
        self.retryAt = time.time() + 0.200

    def __lt__(self, other: SendingHUDPPacket):
        return self.retryAt < other.retryAt


class RecvingHUDPPacket:
    def __init__(self, packet: HUDPPacket, addrPort: AddrPort):
        self.packet = packet
        self.addrPort = addrPort

    def __lt__(self, other: RecvingHUDPPacket):
        return self.packet.seq < other.packet.seq

class GNSContext:
    def __init__(self):
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq: int = 0
        self.rec: int = 0
        self.ack: int = 0

        self.sendWindow: Queue[SendingHUDPPacket] = Queue(maxsize=MAX_WINDOW_SIZE)
        self.sendBuffer: PriorityQueue[SendingHUDPPacket] = PriorityQueue(maxsize=MAX_BUFFER_SIZE)

        self.recvWindow: PriorityQueue[RecvingHUDPPacket] = PriorityQueue(maxsize=MAX_WINDOW_SIZE)
        self.recvBuffer: Queue[bytes] = Queue(maxsize=MAX_BUFFER_SIZE)

        self.bindAddrPort: AddrPort = None
        self.destAddrPort: AddrPort = None
        self.tempDestAddrPort: AddrPort = None

        self.acceptSemaphore: Semaphore = Semaphore(0)
        self.connectSemaphore: Semaphore = Semaphore(0)
