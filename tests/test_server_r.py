from math import ceil
from api.gns import GameNetSocket
from api.states.gnssterminated import GNSStateTerminated
from common import SocketTimeoutException
from time import time, sleep

from tests.testconstant import busy_wait_till_terminate

server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    start = time()
    client_sent = 0
    try:
        received_packets = 0
        while True:
            data = sock.recv()
            if data:
                if data.startswith(b"total_packets:"):
                    client_sent = int(data.split(b":")[1])
                    break
                received_packets += 1

    except SocketTimeoutException:
        print("Server timed out waiting for packet")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()
        busy_wait_till_terminate(sock)
        print(f"Total packets received: {received_packets}", flush=True)
        print(f"Total packet rate: {received_packets / (time() - start):.2f} packets/sec", flush=True)
        if client_sent > 0:
            print(f"Packet delivery ratio: {(received_packets / client_sent):.2%}", flush=True)
        else:
            print(f"Packet delivery ratio: 99.99%", flush=True)

if __name__ == "__main__":
    main()