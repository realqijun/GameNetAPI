from api.gns import GameNetSocket
from common import SocketTimeoutException

server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    # server accepted a connection

    try:
        # receive hello message
        data = sock.recv()
        if not data:
            raise Exception("Client disconnected before sending hello")
        print(f"Received first message: {data}")

        received_packets = 0
        with open("tests/test_cases/2.txt", "r") as f:
            data = f.readlines()
            expected_len = len(data)

            for i in range(expected_len):
                recv_data = sock.recv()
                if not data:
                    print("Client disconnected early")
                    break
                assert recv_data == data[i].encode() # check if they are in order
                received_packets += 1

        print(f"Received {received_packets}/{expected_len} packets")

    except SocketTimeoutException:
        print("Server timed out waiting for packet")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()
        print("Server closed.")

if __name__ == "__main__":
    main()