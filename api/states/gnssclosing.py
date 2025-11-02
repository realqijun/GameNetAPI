import time

from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext, SendingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from api.states.gnsstimewait import GNSStateTimeWait
from hudp import HUDPPacket


class GNSStateClosing(GNSState):
    """
    CLOSING happens during a simultaneous close, when a FIN packet is sent out and a FIN packet is received
    from remote before the expected ACK.

    In this state, the socket waits for the expected ACK to come and transition into TIME_WAIT.
    We must still handle all other data packets and ACKs here as some packets from remote may be
    lost and are re-transmitted.

    All other packets are dropped and ignored.
    """

    def __init__(self):
        self.timeOnCurrentAck = time.time()
        """
        The last time when ACK changed.
        """

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureAck() and packet.ack == context.seq:
                context.rec = packet.ack
                context.closeSemaphore.release()
                return GNSStateTimeWait()
            elif packet.isSynAck() and packet.seq + 1 == context.ack:
                context.sendWindow.put(SendingHUDPPacket(HUDPPacket.createPureAck(context.rec, context.ack)))
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
