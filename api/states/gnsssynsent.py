from api.states.gnsstate import GNSState
from api.states.gnssestablished import GNSStateEstablished
from api.states.gnsssynrcvd import GNSStateSynRcvd
from api.states.gnssinitial import GNSStateInitial
from api.gnscontext import GNSContext, SendingHUDPPacket
from hudp import HUDPPacket


class GNSStateSynSent(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isSynAck() and packet.ack == context.seq:
                context.ack = packet.seq + 1
                context.rec = packet.ack
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
                context.connectSemaphore.release()
                return GNSStateEstablished()
            elif packet.isPureSyn():  # Simultaneous open
                context.ack = packet.ack + 1
                synAck = HUDPPacket.create(context.seq, context.ack, bytes(), isReliable=True, isSyn=True, isAck=True)
                context.seq += 1
                context.sendWindow.put(SendingHUDPPacket(synAck))
                return GNSStateSynRcvd()
            elif packet.isRst() and packet.ack == context.seq:
                return GNSStateInitial()

        return self
