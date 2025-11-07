from api.gns import GameNetSocket
from time import sleep
import random

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt", "tests/test_cases/2.txt", "tests/test_cases/3.txt"]

def main():
    client = GameNetSocket()
    client.bind(client_addr)
    client.connect(server_addr)
    sleep(0.5)
    # hopefully prints rtt after this

    # client connected

    chunk = 1024

    for test_file in tests:
        with open(test_file, "r") as f:
            data = f.read()
            while data:
                reliable = random.choice([True, False])
                client.send(data[:chunk].encode(), reliable)
                data = data[chunk:]
                sleep(0.1)

    # all data sent
    client.close()

if __name__ == "__main__":
    main()