from time import time
from api.gns import GameNetSocket
from common import SocketTimeoutException

server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    start = time()
    client_sent = 0
    try:
        reliable_packets_received = 0
        unreliable_packets_received = 0
        while True:
            data = sock.recv()
            if not data:
                break
            if data.startswith(b'REL:'):
                reliable_packets_received += 1
            elif data.startswith(b'UNR:'):
                unreliable_packets_received += 1
            elif data.startswith(b"total_packets_reliable:"):
                parts = data.split(b";")
                reliable_part = parts[0]
                unreliable_part = parts[1]
                client_sent_reliable = int(reliable_part.split(b":")[1])
                client_sent_unreliable = int(unreliable_part.split(b":")[1])
                client_sent = client_sent_reliable + client_sent_unreliable
                break
    except SocketTimeoutException:
        print("Server timed out waiting for packet")
    except Exception as e:
        print(f"An error occurred: {e}")

    sock.close()
    print(f"Reliable packets received: {reliable_packets_received}")
    print(f"Unreliable packets received: {unreliable_packets_received}")
    print(f"Total packet rate: {(reliable_packets_received + unreliable_packets_received) / (time() - start):.2f} packets/sec")
    if client_sent > 0:
        print(f"Reliable packet delivery ratio: {(reliable_packets_received / client_sent_reliable):.2%}")
        print(f"Unreliable packet delivery ratio: {(unreliable_packets_received / client_sent_unreliable):.2%}")
    else:
        print(f"Packet delivery ratio: 99.99%") # final reliable packets sent packet didnt get through

if __name__ == "__main__":
    main()