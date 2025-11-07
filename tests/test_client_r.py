from api.gns import GameNetSocket
from time import sleep

client_addr = ("127.0.0.1", 4896)
server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt", "tests/test_cases/2.txt", "tests/test_cases/3.txt"]

def main():
    client = GameNetSocket()
    client.bind(client_addr)
    client.connect(server_addr)
    sleep(0.5)
    # hopefully prints rtt after this

    # client connected

    # test empty data and single byte
    client.send(b"", True)
    client.send(b"a", True)
    sleep(0.5)
    # look for rtt print

    chunk = 1024
    reliable_packets_sent = 2  # already sent 2 packets above

    for file in tests:
        with open(file, "r") as f:
            data = f.read()
            while data:
                client.send(data[:chunk].encode(), True)  # reliable send
                reliable_packets_sent += 1
                data = data[chunk:]
                sleep(0.1) # sleep to avoid overwhelming the server, remove if dont want to see acks

    # all data sent
    client.close()
    print(f"Reliable packets sent: {reliable_packets_sent}")
    
if __name__ == "__main__":
    main()