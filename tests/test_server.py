from api.gns import GameNetSocket

if __name__ == "__main__":
    server = GameNetSocket()
    server.bind(('localhost', 54321))
    server.connect(('127.0.0.1', 12345))
    for i in range(1000):
        print(i, server.recv().decode(encoding='utf-8'), flush=True)
    server.close()