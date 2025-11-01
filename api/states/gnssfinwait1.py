from api.states.gnssclosing import GNSStateClosing
from api.states.gnsstate import GNSState
from api.states.gnssfinwait2 import GNSStateFinWait2
from api.gnscontext import GNSContext, SendingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from hudp import HUDPPacket
import time


class GNSStateFinWait1(GNSState):
    """
    FIN_WAIT1 happens after user calls close() on the socket and a FIN was sent to remote. This state
    essentially waits for the expected ACK to come back.

    In this state, there are several special cases to consider:

    - SYN ACK: sends the appropriate ACK back to remote. This happens when previous ACKs are lost.
    - FIN: sends the appropriate ACK back to remote, notice the simultaneous close and transition into CLOSING.
    - RST: terminates the connection immediately.
    - Pure ACK matching the previously sent FIN packet: transition into FIN_WAIT2.
    - Other pure ACK: updates largest received ACK.
    - Data packets: processes each on in-order and update REC and ACK accordingly. If the socket
      is stuck on an ACK for too long, it will automatically go to the nearest next SEQ that it has received.

    All other packets are dropped and ignored.
    """

    def __init__(self):
        self.timeOnCurrentAck = time.time()
        """
        The last time when ACK changed.
        """

    def process(self, context: GNSContext) -> GNSState:
        initialAck = context.ack

        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isSynAck() and packet.seq + 1 == context.ack:
                ack = HUDPPacket.create(context.rec, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
            elif packet.isFin() and packet.seq == context.ack:  # Simultaneous close
                context.ack = packet.seq + 1
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
                return GNSStateClosing()
            elif packet.isRst() and packet.seq == context.ack:
                return GNSStateTerminated()
            elif packet.isPureAck() and packet.ack == context.seq:
                context.rec = packet.ack
                context.closeSemaphore.release()
                return GNSStateFinWait2()
            elif packet.isPureAck():
                context.rec = max(context.rec, packet.ack)
            elif packet.isDataPacket():
                if packet.seq < context.ack:
                    # We have acknowledged this packet before, skip it.
                    continue
                elif packet.seq > context.ack:
                    # If this packet is out-in-order, all packets after it are out-of-order too
                    # due to the ordering of the PriorityQueue
                    context.recvWindow.put(recvingPacket)
                    break
                else:
                    context.rec = max(context.rec, packet.ack)
                    context.ack = packet.calculateAck()
                    self.timeOnCurrentAck = time.time()
                    context.recvBuffer.put(packet.content)

        # If ACK changed or a data packet was received, send back a pure ACK
        if initialAck < context.ack or context.receivedPacket:
            context.receivedPacket = False
            ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
            context.sendWindow.put(SendingHUDPPacket(ack))

        currentTime = time.time()
        # The socket has been stuck on this ACK for too long, skip ACK to the nearest next SEQ
        # that it has received
        if currentTime - self.timeOnCurrentAck > 1.000 and context.recvWindow.qsize() > 0:
            recvingPacket = context.recvWindow.get()
            context.ack = recvingPacket.packet.seq
            context.recvWindow.put(recvingPacket)

        return self
