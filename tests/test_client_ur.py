import os
from api.gns import GameNetSocket
from time import sleep, time
import random

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

    reliable_packets_sent = 0
    unreliable_packets_sent = 0
    packet = os.urandom(1019)

    while time() < end_time:
        reliable = random.choice([True, False])
        if reliable:
            sock.send((b'REL:' + packet), reliable)  # reliable send
            reliable_packets_sent += 1
        else:
            sock.send((b'UNR:' + packet), reliable)  # unreliable send
            unreliable_packets_sent += 1

        next_send_time = start_time + ((reliable_packets_sent + unreliable_packets_sent) * interval)
        sleep_duration = next_send_time - time()

        if sleep_duration > 0:
            sleep(sleep_duration)

    sock.send(b"total_packets_reliable:" + str(reliable_packets_sent).encode() + b";total_packets_unreliable:" + str(unreliable_packets_sent).encode(), True)
    # all data sent
    sock.close()
    print(f"Reliable packets sent: {reliable_packets_sent}")
    print(f"Unreliable packets sent: {unreliable_packets_sent}")

if __name__ == "__main__":
    main()