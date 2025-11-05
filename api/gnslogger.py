from api.gnscontext import SendingHUDPPacket
from hudp import HUDPPacket
from typing import Dict, List, Deque, Tuple
from datetime import datetime
from statistics import mean
import time


WINDOW = 0.500


class GNSLogger:
    def __init__(self, logSend=True, logRecv=True, logMetrics=True):
        self.sendRecord: Dict[int, float] = {}
        """
        Tracks all packet that has been sent.
        Maps the SEQ of the packet to the timestamp when it was first sent.
        """

        self.recvRecord: Dict[int, float] = {}
        """
        Tracks all valid packet that has been received.
        Maps the SEQ of the packet to the timestamp when it was first received.
        """

        self.latencies: Deque[Tuple[float, int]] = []
        self.totalLatencies = 0
        self.jitters: Deque[Tuple[float, int]] = []
        self.totalJitters = 0
        self.dataSizes: Deque[Tuple[float, int]] = []
        self.totalDataSizes = 0

        self.lastAck: int = 0

        self.enableLogSend = logSend
        self.enableLogRecv = logRecv
        self.enableLogMetrics = logMetrics

    def setEnableLogSend(self, newValue: bool):
        self.enableLogSend = newValue

    def setEnableLogRecv(self, newValue: bool):
        self.enableLogRecv = newValue

    def setEnableLogMetrics(self, newValue: bool):
        self.enableLogMetrics = newValue

    def log(self, message: str):
        timeString = datetime.now().strftime("%M:%S:%f")[:-3]
        print(f"[{timeString}]: \033[43m API \033[0m {message}", flush=True)

    def logInfo(self, message: str):
        timeString = datetime.now().strftime("%M:%S:%f")[:-3]
        print(f"[{timeString}]: \033[43m API \033[0m \033[100m INFO \033[0m {message}", flush=True)

    def logSend(self, sendingPacket: SendingHUDPPacket):
        packet = sendingPacket.packet
        message = f"\033[42m SEND \033[0m {packet} "
        if not packet.isUnreliable():
            if packet.seq in self.sendRecord:
                message += "retransmit "
            else:
                self.sendRecord[packet.seq] = packet.time

        if self.enableLogSend:
            self.log(message)

    def logRecv(self, packet: HUDPPacket):
        message = f"\033[44m RECV \033[0m {packet} "
        if not packet.isUnreliable():
            if packet.seq in self.recvRecord:
                message += "duplicate "
            else:
                self.recvRecord[packet.seq] = packet.time

        if self.enableLogRecv:
            self.log(message)

        if packet.flags.isAck and packet.ack > self.lastAck:
            rtt = round((packet.time - self.sendRecord[self.lastAck]) * 1000)
            if self.enableLogMetrics:
                self.logInfo(f"SEQ {self.lastAck} -> {packet.ack}: RTT ≈ {rtt} ms")
            self.lastAck = packet.ack

        currentTime = time.time()
        latency = currentTime - packet.time
        self.totalLatencies += latency
        self.latencies.append((currentTime, latency))
        if len(self.latencies) > 0:
            jitter = abs(latency - self.jitters[-1])
            self.totalJitters += jitter
            self.jitters.append((currentTime, jitter))
        self.totalDataSizes += len(packet.content)
        self.dataSizes.append((currentTime, len(packet.content)))

        self.__updateRunningMetrics()

    def __updateRunningMetrics(self):
        currentTime = time.time()
        while self.latencies[0] < currentTime - WINDOW:
            self.totalLatencies -= self.latencies.popleft()[1]
        while self.jitters[0] < currentTime - WINDOW:
            self.totalJitters -= self.jitters.popleft()[1]
        while self.dataSizes[0] < currentTime - WINDOW:
            self.totalDataSizes -= self.dataSizes.popleft()[1]

    def __printRunningMetrics(self):
        self.printInfo((
            f"Past {WINDOW} seconds, "
            f"Average Latency: {self.totalLatencies / len(self.latencies)} | "
            f"Jitter: {self.totalJitters / len(self.totalJitters)} | "
            f"Throughput: {self.totalDataSizes}"
        ))
