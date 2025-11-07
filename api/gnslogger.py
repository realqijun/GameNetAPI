from api.gnscontext import SendingHUDPPacket
from hudp import HUDPPacket
from typing import Dict, List, Tuple
from datetime import datetime
from functools import reduce
from statistics import mean
import time


class Metrics:
    def __init__(self):
        self.latencies: List[int] = []
        self.jitters: List[int] = []
        self.dataSizes: List[Tuple[float, int]] = []
        self.lastTransitTime = 0
        self.currentJitter = 0

    def updateMetrics(self, packet: HUDPPacket):
        currentTime = time.time()
        latency = currentTime - packet.time

        if hasattr(self, 'lastTransitTime') and self.lastTransitTime > 0:
            # RFC 3550 jitter calculation
            D = latency - self.lastTransitTime
            self.currentJitter += (abs(D) - self.currentJitter) / 16
            self.jitters.append(self.currentJitter)

        self.lastTransitTime = latency
        self.latencies.append(latency)
        self.dataSizes.append((currentTime, len(packet.toBytes())))

    def __str__(self):
        avgLatency = 0
        if len(self.latencies) > 0:
            avgLatency = round(mean(self.latencies) * 1000)

        jitter = 0
        if len(self.jitters) > 0:
            jitter = round(mean(self.jitters) * 1000)

        throughput = 0
        if len(self.dataSizes):
            totalTime = self.dataSizes[-1][0] - self.dataSizes[0][0]
            if totalTime > 0:
                totalDataSizes = reduce(lambda acc, tup: acc + tup[1], self.dataSizes, 0)
                throughput = round(totalDataSizes / totalTime)

        return (
            f"Average Latency: {avgLatency} ms | "
            f"Jitter: {jitter} ms | "
            f"Throughput: {throughput} Bps"
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
        self.log(f"\033[100m INFO \033[0m {message}")

    def logMtrc(self, message: str):
        self.log(f"\033[45m MTRC \033[0m {message}")

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
            rtt = round((time.time() - self.sendSeqRecord[self.lastAck]) * 1000)
            if self.enableLogMetrics:
                self.logMtrc(f"SEQ {self.lastAck} -> {packet.ack}: RTT ≈ {rtt} ms")
            self.lastAck = packet.ack

        if packet.isUnreliable():
            self.unreliableMetrics.updateMetrics(packet)
        else:
            self.reliableMetrics.updateMetrics(packet)

    def logMetrics(self):
        if self.enableLogMetrics:
            self.logInfo(f"Unreliable: {self.unreliableMetrics}")
            self.logInfo(f"Reliable: {self.reliableMetrics}")
