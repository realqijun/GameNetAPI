from api.gnscontext import SendingHUDPPacket
from hudp import HUDPPacket
from typing import Dict, List, Deque, Tuple
from datetime import datetime
import time


class Metrics:
    def __init__(self):
        self.latencies: Deque[Tuple[float, int]] = Deque()
        self.totalLatencies = 0
        self.jitters: Deque[Tuple[float, int]] = Deque()
        self.totalJitters = 0
        self.dataSizes: Deque[Tuple[float, int]] = Deque()
        self.totalDataSizes = 0

    def updateMetrics(self, packet: HUDPPacket):
        currentTime = time.time()

        latency = currentTime - packet.time
        self.totalLatencies += latency
        self.latencies.append((currentTime, latency))
        if len(self.latencies) > 0:
            jitter = abs(latency - self.latencies[-1][1])
            self.totalJitters += jitter
            self.jitters.append((currentTime, jitter))
        self.totalDataSizes += len(packet.content)
        self.dataSizes.append((currentTime, len(packet.content)))

    def __str__(self):
        return (
            f"Average Latency: {round(self.totalLatencies / len(self.latencies) * 1000)} ms | "
            f"Jitter: {round(self.totalJitters / len(self.jitters) * 1000)} ms | "
            f"Throughput: {round(self.totalDataSizes / (self.dataSizes[-1][0] - self.dataSizes[0][0]))} Bps"
        )


class GNSLogger:
    def __init__(self, logSend=True, logRecv=True, logMetrics=True):
        self.sendRecord: Dict[HUDPPacket, float] = {}
        """
        Tracks all packet that has been sent.
        Maps the packet to the timestamp when it was first sent.
        """

        self.sendSeqRecord: Dict[int, float] = {}
        """
        Tracks all packet that has been sent.
        Maps the packet SEQ to the timestamp when it was first sent.
        """

        self.recvRecord: Dict[HUDPPacket, float] = {}
        """
        Tracks all valid packet that has been received.
        Maps the packet to the timestamp when it was first received.
        """

        self.lastAck: int = 0

        self.unreliableMetrics = Metrics()
        self.reliableMetrics = Metrics()

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
            if packet in self.sendRecord:
                message += "retransmit "
            else:
                self.sendRecord[packet] = packet.time
                if packet.seq not in self.sendSeqRecord:
                    self.sendSeqRecord[packet.seq] = packet.time

        if self.enableLogSend:
            self.log(message)

    def logRecv(self, packet: HUDPPacket):
        message = f"\033[44m RECV \033[0m {packet} "
        if not packet.isUnreliable():
            if packet in self.recvRecord:
                message += "duplicate "
            else:
                self.recvRecord[packet] = packet.time

        if self.enableLogRecv:
            self.log(message)

        if packet.flags.isAck and packet.ack > self.lastAck:
            rtt = round((packet.time - self.sendSeqRecord[self.lastAck]) * 1000)
            if self.enableLogMetrics:
                self.logInfo(f"SEQ {self.lastAck} -> {packet.ack}: RTT ≈ {rtt} ms")
            self.lastAck = packet.ack

        if packet.isUnreliable():
            self.unreliableMetrics.updateMetrics(packet)
        else:
            self.reliableMetrics.updateMetrics(packet)

    def logMetrics(self):
        self.logInfo(f"{self.unreliableMetrics}")
        self.logInfo(f"{self.reliableMetrics}")
