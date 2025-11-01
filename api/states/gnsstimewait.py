from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext, SendingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from hudp import HUDPPacket
import time


class GNSStateTimeWait(GNSState):
    def __init__(self):
        self.initialTime = time.time()

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureFin() and packet.seq + 1 == context.ack:
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))

        if time.time() - self.initialTime > 120.000:
            return GNSStateTerminated()

        return self