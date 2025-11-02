from api.states.gnsstate import GNSState
from api.states.gnssterminated import GNSStateTerminated
from api.states.gnsstimewait import GNSStateTimeWait
from api.gnscontext import GNSContext, SendingHUDPPacket
from hudp import HUDPPacket
import time


class GNSStateFinWait2(GNSState):
    """
    FIN_WAIT2 happens after FIN_WAIT1 and the socket is waiting for remote to send FIN.

    In this state, there are several special cases to consider:

    - SYN ACK: sends the appropriate ACK back to remote. This happens when previous ACKs are lost.
    - FIN: sends the appropriate ACK back to remote and transition into TIME_WAIT.
    - RST: terminates the connection immediately.
    - Pure ACK: updates largest received ACK.
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
                context.sendWindow.put(SendingHUDPPacket(HUDPPacket.createPureAck(context.rec, context.ack)))
            elif packet.isFin() and packet.seq == context.ack:
                context.ack = packet.seq + 1
                context.sendWindow.put(SendingHUDPPacket(HUDPPacket.createPureAck(context.seq, context.ack)))
                return GNSStateTimeWait()
            elif packet.isRst() and packet.seq == context.ack:
                return GNSStateTerminated()
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
                    context.shouldSendAck = True
                    context.recvBuffer.put(packet.content)

        currentTime = time.time()
        # The socket has been stuck on this ACK for too long, skip ACK to the nearest next SEQ
        # that it has received
        if currentTime - self.timeOnCurrentAck > 1.000 and context.recvWindow.qsize() > 0:
            recvingPacket = context.recvWindow.get()
            context.ack = recvingPacket.packet.seq
            context.recvWindow.put(recvingPacket)

        return self
