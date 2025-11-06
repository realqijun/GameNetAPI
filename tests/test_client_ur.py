from api.gns import GameNetSocket
from time import sleep
import random

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)

def main():
    client = GameNetSocket()
    client.bind(client_addr)
    client.connect(server_addr)
    sleep(0.5)
    # hopefully prints rtt after this

    # client connected

    with open("tests/test_cases/3.txt", "r") as f:
        data = f.readlines()
        reliable = True
        for line in data:
            client.send(line.encode(), reliable)
            if random.random() <= 0.7:
                reliable = not reliable

    # all data sent
    client.close()

if __name__ == "__main__":
    main()