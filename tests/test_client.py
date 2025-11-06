from api.gns import GameNetSocket
from time import sleep

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)

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

    with open("tests/test_cases/2.txt", "r") as f:
        data = f.readlines() # cant send entire file because underlying udp layer max payload is 65507 bytes
        for line in data:
            client.send(line.encode(), True) # reliable send
            sleep(0.01) # slight delay to avoid overwhelming the server

    # all data sent
    client.close()

if __name__ == "__main__":
    main()