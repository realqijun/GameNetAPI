from api.gns import GameNetSocket
from common import SERVER_PORT, FORWARDER_PORT
import time


def main():
    try:
        sock = GameNetSocket()
        sock.bind(('127.0.0.1', SERVER_PORT))
        sock.listen()
        sock.accept()
        # sock.connect(('127.0.0.1', FORWARDER_PORT))


    # Main receive loop
        while True:
            try:
                message = sock.recv().decode('utf-8')
                print(message, flush=True)
            except KeyboardInterrupt:
                print("Server shutting down...")
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Clean up
        if sock:
            sock.close()

if __name__ == "__main__":
    main()
    while True:
        print(sock.recv().decode(encoding='utf-8'), flush=True)

    
    # for i in range(100):
    #     sock.send(f"I am Minh from server {i}".encode('utf-8'), True)
    # sock.close()
    # for i in range(100):
    #     print(sock.recv().decode(encoding='utf-8'), flush=True)


main()
