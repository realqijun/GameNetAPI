from hudp import HUDPPacket

content = b"I am Minh"
packet = HUDPPacket.create(1, 1, content, isReliable=True, isAck=True)
# other = HUDPPacket.create(1000, 1001, True, False, True, True)
data = packet.toBytes()
print(HUDPPacket.checksum1s(data))
print(HUDPPacket.fromBytes(data))
print(HUDPPacket.fromBytes(data).content.decode(encoding='utf-8'))

