from api import GameNetAPI
from common import CLIENT_PORT, FORWARDER_PORT


def main():
    api = GameNetAPI()
    api.bind('127.0.0.1', CLIENT_PORT)
    api.listen()
    data = b"Hello!"
    for i in range(0, 5):
        api.send(data, True)


main()
