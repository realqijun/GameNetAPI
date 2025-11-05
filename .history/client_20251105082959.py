from api.gns import GameNetSocket
from common import FORWARDER_PORT, CLIENT_PORT
import time

def main():
    sock = None
    try:
        sock = GameNetSocket()
        sock.bind(('127.0.0.1', CLIENT_PORT))
        sock.connect(('127.0.0.1', FORWARDER_PORT))
        
        print("Client connected, sending messages...")
        for i in range(100):
            message = f"I am Minh {i}"
            sock.send(message.encode('utf-8'), True)
            print(f"Sent: {message}")
            time.sleep(0.1)  # Small delay to prevent flooding
            
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        if sock:
            sock.close()

if __name__ == "__main__":
    main()