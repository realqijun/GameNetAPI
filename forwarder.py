from hudp import HUDPPacket
import socket
import random

CLIENT_PORT = 50000
SERVER_PORT = 60000


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 55000))
    while True:
        data, address = sock.recvfrom(16384)
        packet = HUDPPacket.fromBytes(data)
        print(packet)
        if address[1] == CLIENT_PORT:
            if packet.flags.isSyn and random.random() < 0.4:
                print("DROPPED")
                continue
            if packet.flags.isAck and random.random() < 0.4:
                print("DROPPED")
                continue
            sock.sendto(data, ('127.0.0.1', SERVER_PORT))
        elif address[1] == SERVER_PORT:
            if packet.flags.isSyn and packet.flags.isAck and random.random() < 0.4:
                print("DROPPED")
                continue
            sock.sendto(data, ('127.0.0.1', CLIENT_PORT))
        else:
            print(address)
            print("NOT SUPPOSED TO HAPPEN")

        print()


main()
