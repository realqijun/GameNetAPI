from api.gns import GameNetSocket
from time import sleep

client_addr = ("127.0.0.1", 9999)
server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(client_addr)
    sock.connect(server_addr)

    # client connected

    with open("tests/test_cases/1.txt", "r") as f:
        data = f.readlines()
        for line in data:
            sock.send(line.encode(), False) # unreliable send
            sleep(0.01) # slight delay to avoid overwhelming the server

    sock.close()

if __name__ == "__main__":
    main()