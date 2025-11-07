from api.gns import GameNetSocket
from time import sleep

client_addr = ("127.0.0.1", 9999)
server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt", "tests/test_cases/2.txt", "tests/test_cases/3.txt"]

def main():
    sock = GameNetSocket()
    sock.bind(client_addr)
    sock.connect(server_addr)

    # client connected

    chunk = 1024

    for test_file in tests:
        with open(test_file, "r") as f:
            data = f.read()
            while data:
                sock.send(data[:chunk].encode(), False)  # unreliable send
                data = data[chunk:]
                sleep(0.1)

    sock.close()

if __name__ == "__main__":
    main()