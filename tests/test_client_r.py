from api.gns import GameNetSocket
from time import sleep, time

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt", "tests/test_cases/2.txt", "tests/test_cases/3.txt", "tests/test_cases/4.txt"]
# tests = ["tests/test_cases/3.txt"]

def main():
    client = GameNetSocket()
    client.bind(client_addr)
    client.connect(server_addr)
    sleep(0.5)
    # hopefully prints rtt after this

    target_rate = 100
    interval = 1.0 / target_rate

    # # test empty data and single byte
    # client.send(b"", True)
    # client.send(b"a", True)

    # sleep(0.1)
    # # look for rtt print

    chunk = 1024
    packets_sent = 0  # already sent 2 packets above

    for file in tests:
        with open(file, "r") as f:

            data = f.read()

            # while data:
            #     next_time_to_send = time() + 1.0
            #     for i in range(50):
            #         if len(data) == 0:
            #             break
            #         client.send(data[:chunk].encode(), True)  # reliable send
            #         data = data[chunk:]
            #         packets_sent += 1

            #     if time() < next_time_to_send:
            #         sleep(next_time_to_send - time())
            next_time_to_send = time()
            while data:
                # current_time = time()
                while time() < next_time_to_send:
                    continue
                # if current_time < next_time_to_send:
                #     sleep(next_time_to_send - current_time)
                client.send(data[:chunk].encode(), True)  # reliable send
                data = data[chunk:]
                packets_sent += 1
                next_time_to_send = time() + interval

    # all data sent
    client.close()
    print(f"Reliable packets sent: {packets_sent}")

if __name__ == "__main__":
    main()
