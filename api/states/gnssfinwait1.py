from api.states.gnssclosing import GNSStateClosing
from api.states.gnsstate import GNSState
from api.states.gnssfinwait2 import GNSStateFinWait2
from api.gnscontext import GNSContext, SendingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from hudp import HUDPPacket
import time


class GNSStateFinWait1(GNSState):
    def __init__(self):
        self.timeOnCurrentAck = time.time()

    def process(self, context: GNSContext) -> GNSState:
        initialAck = context.ack

        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureAck() and packet.ack == context.seq:
                context.rec = packet.ack
                context.closeSemaphore.release()
                return GNSStateFinWait2()
            elif packet.isPureFin() and packet.seq == context.ack:
                context.ack = packet.seq + 1
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
                return GNSStateClosing()
            elif packet.isSynAck() and packet.seq + 1 == context.ack:
                ack = HUDPPacket.create(context.rec, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
            elif packet.isRst() and packet.seq == context.ack:
                return GNSStateTerminated()
            elif packet.isPureAck():
                context.rec = max(context.rec, packet.ack)
            elif packet.isDataPacket():
                if packet.seq < context.ack:
                    continue
                elif packet.seq > context.ack:
                    context.recvWindow.put(recvingPacket)
                    break
                else:
                    context.rec = max(context.rec, packet.ack)
                    context.ack = packet.calculateAck()
                    self.timeOnCurrentAck = time.time()
                    context.recvBuffer.put(packet.content)

        if initialAck < context.ack or context.receivedPacket:
            context.receivedPacket = False
            ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
            context.sendWindow.put(SendingHUDPPacket(ack))

        currentTime = time.time()
        if currentTime - self.timeOnCurrentAck > 1.000 and context.recvWindow.qsize() > 0:
            recvingPacket = context.recvWindow.get()
            context.ack = recvingPacket.packet.seq
            context.recvWindow.put(recvingPacket)

        return self