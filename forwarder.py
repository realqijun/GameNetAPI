from hudp import HUDPPacket
from common import CLIENT_PORT, SERVER_PORT, FORWARDER_PORT
from datetime import datetime
import socket
import random


def getCurrentTimeString() -> str:
    timeString = datetime.now().strftime("%M:%S:%f")[:-3]
    return f"[{timeString}]"


def printDropped() -> None:
    return print("\033[41m DROPPED \033[0m", end='')


def handleClientPacket(sock: socket.socket, data: bytes, dropRate: float):
    if random.random() < dropRate:
        printDropped()
        return
    sock.sendto(data, ('127.0.0.1', SERVER_PORT))


def handleServerPacket(sock: socket.socket, data: bytes, dropRate: float):
    if random.random() < dropRate:
        printDropped()
        return
    sock.sendto(data, ('127.0.0.1', CLIENT_PORT))


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', FORWARDER_PORT))
    while True:
        data, address = sock.recvfrom(16384)
        packet = HUDPPacket.fromBytes(data)
        if address[1] == CLIENT_PORT:
            print(f"{getCurrentTimeString()} C -> S: {packet}", end='')
            handleClientPacket(sock, data, 0.5)
        elif address[1] == SERVER_PORT:
            print(f"{getCurrentTimeString()} S -> C: {packet}", end='')
            handleServerPacket(sock, data, 0.5)
        else:
            print("NOT SUPPOSED TO HAPPEN")

        print()


main()
