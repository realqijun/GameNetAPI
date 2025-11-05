from __future__ import annotations
from datetime import datetime
import struct
import time


class HUDPFlags:
    """
    Represent the flags portion of the HUDP packet header.
    """

    def __init__(self, isReliable: bool, isAck: bool, isSyn: bool, isFin: bool, isRst: bool):
        self.isReliable = isReliable
        """True if the packet is on the reliable channel. False otherwise"""

        self.isAck = isAck
        """True if the ACK field is significant. False otherwise"""

        self.isSyn = isSyn
        """True if the packet is trying to establish connection. False otherwise"""

        self.isFin = isFin
        """True if the packet is trying to terminate connection. False otherwise"""

        self.isRst = isRst
        """True if the packet is meant to reset the connection. False otherwise"""

    @classmethod
    def fromBytes(cls, data: bytes) -> HUDPFlags:
        """
        Reconstruct flags from its bytes' representation.
        """
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
        """
        Convert flags into its 16-bit integer representation.
        """
        return (self.isReliable << 4) + (self.isAck << 3) + (self.isSyn << 2) + (self.isFin << 1) + self.isRst

    def toBytes(self) -> bytes:
        """
        Convert flags into its bytes' representation.
        """
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
        return string[:-1]  # -1 to remove the last space from the string


class HUDPPacket:
    """
    Represent the entire HUDP packet.
    """

    def __init__(self, time: int, seq: int, ack: int, checksum: int, flags: HUDPFlags, content: bytes):
        self.time = time
        """ Timestamp in milliseconds when this packet was created """

        self.seq = seq
        """ Sequence Number of the packet """

        self.ack = ack
        """ Acknowledgement Number of the packet """

        self.checksum = checksum
        """ 16-bit 1s complement checksum of the packet """

        self.flags = flags
        """ Flags of the packet """

        self.content = content
        """ Content of the packet in bytes """

    @staticmethod
    def checksum1s(data: bytes) -> int:
        """
        Helper method for calculating 1s complement checksum
        """
        sum: int = 0
        for i in range(len(data) // 2):
            sum += (data[2 * i] << 8) + data[2 * i + 1]
        sum = (sum & 0xFFFF) + (sum >> 16)
        return 0xFFFF - sum

    @staticmethod
    def verifyChecksum(data: bytes) -> bool:
        """
        Helper method for validating 1s complement checksum
        """
        return HUDPPacket.checksum1s(data) == 0

    @classmethod
    def fromBytes(cls, data: bytes) -> HUDPPacket:
        """
        Reconstruct the packet from its bytes' representation.
        """
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
    def create(cls, seq: int, ack: int, content: bytes = bytes(),
               isReliable=False, isAck=False, isSyn=False, isFin=False, isRst=False) -> HUDPPacket:
        """
        Construct a HUDP packet, automatically filling in the current timestamp and checksum.
        Use this method over the __init__ method when creating a HUDP packet.
        """
        flags = HUDPFlags(isReliable, isAck, isSyn, isFin, isRst)
        currentTime = round(time.time() * 1000)
        packet = HUDPPacket(currentTime, seq, ack, 0, flags, content)
        packet.checksum = HUDPPacket.checksum1s(packet.toBytes())
        return packet

    @classmethod
    def createPureAck(cls, seq: int, ack: int) -> HUDPPacket:
        """
        Construct a Pure ACK packet, only meant for delivering ACK to remote.
        """
        return HUDPPacket.create(seq, ack, bytes(), isAck=True)

    def toBytes(self) -> bytes:
        """
        Convert the packet into its bytes' representation.
        """
        packet = (struct.pack("!QIIH", self.time, self.seq, self.ack, self.checksum)
                  + self.flags.toBytes() + self.content)
        assert (len(packet) >= 20)
        return packet

    def isReliable(self) -> bool:
        """
        Return True if packet is reliable. False otherwise.
        """
        return self.flags.isReliable

    def isSynAck(self) -> bool:
        """
        SYN ACK packets in the 3-way handshake have the reliable, syn and ack flags set
        and only those 3. Return True if this packet is a SYN ACK packet. False otherwise.
        """
        return self.flags.toInteger() == 0b0001_1100

    def isSyn(self) -> bool:
        """
        SYN packets in the 3-way handshake have the reliable and syn flags set
        and only those 2. Return True if this packet is a SYN packet. False otherwise.
        """
        return self.flags.toInteger() == 0b0001_0100

    def isPureAck(self) -> bool:
        """
        Pure ACK packets are packets that are only meant to deliver the ACK back to remote.
        They only have the ack flag set. Return True if this packet is a pure ACK packet. False otherwise.
        """
        return self.flags.toInteger() == 0b0000_1000

    def isFin(self) -> bool:
        """
        FIN packets in the 4-way termination handshake have the reliable and fin flags set
        and only those 2. Return True if this packet is a FIN packet. False otherwise.
        """
        return self.flags.toInteger() == 0b0001_0010

    def isRst(self) -> bool:
        """
        RST packets serve to reset the connection with remote. They only have the rst flag set.
        Return True if this packet is a RST packet. False otherwise.
        """
        return self.flags.toInteger() == 0b0000_0001

    def calculateAck(self) -> int:
        """
        Calculate the expected ACK for this packet.
        """
        return self.seq + len(self.content)

    def isUnreliable(self) -> bool:
        """
        Return True if the packet is unreliable. False otherwise.
        """
        return not self.flags.isReliable

    def isDataPacket(self):
        """
        Return True if the packet transfer data. False otherwise.
        """
        return len(self.content) > 0

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
        return (
            f"[{timeString}] SEQ: {self.seq:>5} ACK: "
            f'{self.ack:>5} Flags: {self.flags} {"DATA" if self.isDataPacket() else ""}"
        )

    def __lt__(self, other: HUDPPacket):
        return self.seq < other.seq
