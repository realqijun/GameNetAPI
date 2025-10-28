from api import GameNetAPI


def main():
    api = GameNetAPI()
    api.bind('127.0.0.1', 60000)
    api.accept()


main()
