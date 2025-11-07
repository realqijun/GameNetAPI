import os
from api.gns import GameNetSocket
from time import sleep, time

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)

test_duration = 30
target_rate = 100

def main():
    sock = GameNetSocket()
    sock.bind(client_addr)
    sock.connect(server_addr)
    sleep(0.5)

    interval = 1.0 / target_rate

    start_time = time()
    end_time = start_time + test_duration

    packet_index = 0
    unreliable_sent = 0
    packet = os.urandom(1024)  # 1 KB packet

    while time() < end_time:
        sock.send(packet, False)
        unreliable_sent += 1
        packet_index += 1

        next_send_time = start_time + (packet_index * interval)
        sleep_duration = next_send_time - time()

        if sleep_duration > 0:
            sleep(sleep_duration)

    sock.send(b"total_packets:" + str(unreliable_sent).encode(), True)
    # all data sent
    sock.close()

    print("\n--- CLIENT TEST FINISHED ---")
    print(f"Total packets sent: {unreliable_sent}")

if __name__ == "__main__":
    main()