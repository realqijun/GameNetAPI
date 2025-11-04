from api.gns import GameNetSocket

if __name__ == "__main__":
    sock = GameNetSocket()
    sock.bind(('127.0.0.1', 12345))
    sock.connect(('127.0.0.1', 54321))

    with open('tests/test_cases/1.txt', 'r') as f:
        content = f.read()
        for line in content.splitlines():
            sock.send(line.encode('utf-8'), True)
        sock.close()
