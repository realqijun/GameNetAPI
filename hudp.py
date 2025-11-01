from __future__ import annotations
from datetime import datetime
import struct
import time


class HUDPFlags:
    def __init__(self, isReliable: bool, isAck: bool, isSyn: bool, isFin: bool, isRst: bool):
        self.isReliable = isReliable
        self.isAck = isAck
        self.isSyn = isSyn
        self.isFin = isFin
        self.isRst = isRst

    @classmethod
    def fromBytes(cls, data: bytes) -> HUDPFlags:
        assert (len(data) == 2)

        integerValue = (data[0] << 8) + data[1]
        return HUDPFlags(
            bool((integerValue & 0x0010) >> 4),
            bool((integerValue & 0x0008) >> 3),
            bool((integerValue & 0x0004) >> 2),
            bool((integerValue & 0x0002) >> 1),
            bool(integerValue & 0x0001),
        )

    def toInteger(self) -> int:
        return (self.isReliable << 4) + (self.isAck << 3) + (self.isSyn << 2) + (self.isFin << 1) + self.isRst

    def toBytes(self) -> bytes:
        data = struct.pack("!H", self.toInteger())
        assert (len(data) == 2)
        return data

    def __eq__(self, other: HUDPFlags):
        if not isinstance(other, HUDPFlags):
            return False

        return (
            self.isReliable == other.isReliable and
            self.isAck == other.isAck and
            self.isSyn == other.isSyn and
            self.isFin == other.isFin and
            self.isRst == other.isRst
        )

    def __str__(self):
        string = "Reliable " if self.isReliable else "Unreliable "
        if self.isAck:
            string += "ACK "
        if self.isSyn:
            string += "SYN "
        if self.isFin:
            string += "FIN "
        if self.isRst:
            string += "RST "
        return string


class HUDPPacket:
    def __init__(self, time: int, seq: int, ack: int, checksum: int, flags: HUDPFlags, content: bytes):
        self.time = time
        self.seq = seq
        self.ack = ack
        self.checksum = checksum
        self.flags = flags
        self.content = content

    @staticmethod
    def checksum1s(data: bytes) -> int:
        sum: int = 0
        for i in range(len(data) // 2):
            sum += (data[2 * i] << 8) + data[2 * i + 1]
        sum = (sum & 0xFFFF) + (sum >> 16)
        return 0xFFFF - sum

    @staticmethod
    def verifyChecksum(data: bytes) -> bool:
        return HUDPPacket.checksum1s(data) == 0

    @classmethod
    def fromBytes(cls, data: bytes) -> HUDPPacket:
        assert (len(data) >= 20)

        flags = HUDPFlags.fromBytes(data[18:20])
        packet = HUDPPacket(
            struct.unpack("!Q", data[0:8])[0],
            struct.unpack("!I", data[8:12])[0],
            struct.unpack("!I", data[12:16])[0],
            struct.unpack("!H", data[16:18])[0],
            flags,
            data[20:]
        )

        return packet

    @classmethod
    def create(cls, seq: int, ack: int, content: bytes,
               isReliable=False, isAck=False, isSyn=False, isFin=False, isRst=False) -> HUDPPacket:
        flags = HUDPFlags(isReliable, isAck, isSyn, isFin, isRst)
        currentTime = round(time.time() * 1000)
        packet = HUDPPacket(currentTime, seq, ack, 0, flags, content)
        packet.checksum = HUDPPacket.checksum1s(packet.toBytes())
        return packet

    def toBytes(self) -> bytes:
        packet = struct.pack("!QIIH", self.time, self.seq, self.ack, self.checksum) + self.flags.toBytes() + self.content
        assert (len(packet) >= 20)
        return packet

    def isSynAck(self) -> bool:
        return self.flags.toInteger() == 0b0001_1100

    def isSyn(self) -> bool:
        return self.flags.toInteger() == 0b0001_0100

    def isAck(self) -> bool:
        return self.flags.toInteger() == 0b0000_1000

    def isFin(self) -> bool:
        return self.flags.toInteger() == 0b0001_0010

    def isRst(self) -> bool:
        return self.flags.toInteger() == 0b0000_0001

    def calculateAck(self) -> int:
        return self.seq + len(self.content)

    def isUnreliable(self) -> bool:
        return not self.flags.isReliable

    def __eq__(self, other: HUDPPacket):
        if not isinstance(other, HUDPPacket):
            return False

        return (
            self.time == other.time and
            self.seq == other.seq and
            self.ack == other.ack and
            self.checksum == other.checksum and
            self.flags == other.flags and
            self.content == other.content
        )

    def __str__(self):
        time = datetime.fromtimestamp(self.time / 1000)
        timeString = time.strftime("%M:%S:%f")[:-3]
        return f"[{timeString}] SEQ: {self.seq:>5} ACK: {self.ack:>5} Flags: {self.flags}"

    def __lt__(self, other: HUDPPacket):
        return self.seq < other.seq
