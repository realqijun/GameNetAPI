from api.gns import GameNetSocket

server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    # server accepted a connection

    # receive hello message
    data = sock.recv()
    print(f"Received first message: {data}")

    received_packets = 0
    with open("tests/test_cases/2.txt", "r") as f:
        data = f.readlines()
        expected_len = len(data)

        for _ in range(expected_len):
            data = sock.recv()
            received_packets += 1
    sock.close()
    print(f"Received {received_packets}/{expected_len} packets")

if __name__ == "__main__":
    main()