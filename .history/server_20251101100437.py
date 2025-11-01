

def


def main():
    api = GameNetAPI()
    api.bind('127.0.0.1', SERVER_PORT)
    api.listen()
    while True:
        data = api.recv()
        print(data.decode(encoding="utf-8"))

    # parse header

main()