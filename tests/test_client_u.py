import os
from api.gns import GameNetSocket
from time import sleep, time
from tests.testconstant import TEST_DURATION, TARGET_RATE, busy_wait_till_terminate

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(client_addr)
    sock.connect(server_addr)
    sleep(0.5)

    interval = 1.0 / TARGET_RATE

    start_time = time()
    end_time = start_time + TEST_DURATION

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
    busy_wait_till_terminate(sock)
    print(f"Total packets sent: {unreliable_sent}")

if __name__ == "__main__":
    main()