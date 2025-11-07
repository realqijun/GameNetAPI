from api.gns import GameNetSocket
from time import sleep, time
import random

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt",
         "tests/test_cases/2.txt",
         "tests/test_cases/3.txt",
         "tests/test_cases/4.txt",
         "tests/test_cases/5.txt"]

def main():
    client = GameNetSocket()
    client.bind(client_addr)
    client.connect(server_addr)
    sleep(0.5)

    target_rate = 100
    interval = 1.0 / target_rate
    chunk = 1019
    reliable_packets_sent = 0
    unreliable_packets_sent = 0

    for test_file in tests:
        with open(test_file, "r") as f:
            data = f.read()
            next_time_to_send = time()
            while data:
                current_time = time()
                reliable = random.choice([True, False])
                if current_time < next_time_to_send:
                    sleep(next_time_to_send - current_time)
                if reliable:
                    client.send(('REL: ' + data[:chunk]).encode(), reliable)  # reliable send
                    reliable_packets_sent += 1
                else:
                    client.send(('UNR: ' + data[:chunk]).encode(), reliable)  # unreliable send
                    unreliable_packets_sent += 1
                data = data[chunk:]
                next_time_to_send = time() + interval


    # all data sent
    client.close()
    print(f"Reliable packets sent: {reliable_packets_sent}")
    print(f"Unreliable packets sent: {unreliable_packets_sent}")

if __name__ == "__main__":
    main()