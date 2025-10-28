from api import GameNetAPI

FORWARD = 55000


def main():
    api = GameNetAPI()
    api.bind('127.0.0.1', 50000)
    api.connect('127.0.0.1', 55000)


main()
