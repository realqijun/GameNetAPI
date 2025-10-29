from api import GameNetAPI
from common import SERVER_PORT


def main():
    api = GameNetAPI()
    api.bind('127.0.0.1', SERVER_PORT)
    api.accept()


main()
