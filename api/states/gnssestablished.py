from api.states.gnssclosewait import GNSStateCloseWait
from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext, SendingHUDPPacket, RecvingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from hudp import HUDPPacket
import time


class GNSStateEstablished(GNSState):
    def __init__(self):
        self.timeOnCurrentAck = time.time()

    def process(self, context: GNSContext) -> GNSState:
        initialAck = context.ack

        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isSynAck():
                if not (context.ack == packet.seq + 1):
                    continue
                ack = HUDPPacket.create(context.rec, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
            elif packet.isFin():
                if not (context.ack == packet.seq):
                    pass
                context.ack = packet.seq + 1
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
                return GNSStateCloseWait()
            elif packet.isRst():
                if not (context.ack == packet.seq):
                    pass
                return GNSStateTerminated()
            elif packet.isSyn():
                rst = HUDPPacket.create(0, packet.seq + 1, bytes(), isRst=True)
                context.sendWindow.put(SendingHUDPPacket(rst))
            else:
                if context.ack > packet.seq:
                    continue
                elif context.ack < packet.seq:
                    context.recvWindow.put(recvingPacket)
                    break
                else:
                    context.rec = max(context.rec, packet.ack)
                    context.ack = packet.calculateAck()
                    self.timeOnCurrentAck = time.time()
                    context.recvBuffer.put(packet.content)

        if initialAck < context.ack:
            ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
            context.sendWindow.put(SendingHUDPPacket(ack))

        currentTime = time.time()
        if currentTime - self.timeOnCurrentAck > 1.000 and context.recvWindow.qsize() > 0:
            recvingPacket = context.recvWindow.get()
            context.ack = recvingPacket.packet.seq
            context.recvWindow.put(recvingPacket)


        return self