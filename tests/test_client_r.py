from api.gns import GameNetSocket
from time import sleep, time

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt",
         "tests/test_cases/2.txt",
         "tests/test_cases/3.txt",
         "tests/test_cases/4.txt",
         "tests/test_cases/5.txt"]

def main():
    sock = GameNetSocket()
    sock.bind(client_addr)
    sock.connect(server_addr)
    sleep(0.5)
    # hopefully prints rtt after this

    target_rate = 100
    interval = 1.0 / target_rate

    chunk = 1024
    packets_sent = 0

    for file in tests:
        with open(file, "r") as f:
            data = f.read()
            next_time_to_send = time()
            while data:
                while time() < next_time_to_send:
                    continue
                sock.send(data[:chunk].encode(), True)
                data = data[chunk:]
                packets_sent += 1
                next_time_to_send = time() + interval

    # all data sent
    sock.close()
    print(f"Reliable packets sent: {packets_sent}")

if __name__ == "__main__":
    main()
