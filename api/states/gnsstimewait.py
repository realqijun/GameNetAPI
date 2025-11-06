from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext, SendingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from hudp import HUDPPacket
from common import TIME_WAIT_TIME
import time


class GNSStateTimeWait(GNSState):
    """
    TIME_WAIT happens after receiving FIN from remote and sending back the appropriate ACK.

    In this state, the socket waits for 2 MSL (Maximum Segment Lifetime) for any retransmitted FIN
    from remote and sends back the appropriate ACK. This usually happens when the ACKs before are lost.

    All other packets are dropped and ignored.
    """

    def __init__(self):
        self.initialTime = time.time()

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isFin() and packet.seq + 1 == context.ack:
                context.sendWindow.put(SendingHUDPPacket(HUDPPacket.createPureAck(context.seq, context.ack)))

        if time.time() - self.initialTime > TIME_WAIT_TIME:
            return GNSStateTerminated()

        return self
