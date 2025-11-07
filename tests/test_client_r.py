from api.gns import GameNetSocket
from time import sleep

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

    # test single packet
    client.send(b"hello world this is client sending a packet", True)
    sleep(0.5)
    # look for rtt print

    chunk = 1024

    for file in tests:
        with open(file, "r") as f:
            data = f.read()
            while data:
                client.send(data[:chunk].encode(), True)  # reliable send
                data = data[chunk:]
                sleep(0.1)

    # all data sent
    client.close()

if __name__ == "__main__":
    main()