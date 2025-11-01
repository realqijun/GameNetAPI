from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext, SendingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from hudp import HUDPPacket


class GNSStateCloseWait(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isFin() and context.ack == (packet.seq + 1):
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
            elif packet.isRst():
                return GNSStateTerminated()
            elif packet.isSyn() or packet.isSynAck():
                rst = HUDPPacket.create(0, packet.seq + 1, bytes(), isRst=True)
                context.sendWindow.put(SendingHUDPPacket(rst))
            elif len(packet.content) > 0:
                rst = HUDPPacket.create(0, packet.calculateAck(), bytes(), isRst=True)
                context.sendWindow.put(SendingHUDPPacket(rst))

        return self