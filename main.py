from hudp import HUDPPacket

content = "Hello".encode()
packet = HUDPPacket.create(0, 0, bytes(), isReliable=True, isSyn=True, isAck=True)
# other = HUDPPacket.create(1000, 1001, True, False, True, True)
data = packet.toBytes()
print(HUDPPacket.checksum1s(data))
