# You no longer need your GameNetAPI_Receiver.py file.
# You just import the API we discussed.
from gamenetsocket import GameNetSocket
from common import SERVER_PORT

# 1. Create the socket
server_sock = GameNetSocket()

try:
    server_sock.bind(('127.0.0.1', SERVER_PORT))
    server_sock.listen()
    
    print("Server is waiting for a connection...")
    
    # blocking call, waits for a client to connect. completes 3 way handshake and starts all threads
    server_sock.accept() 
    
    print("Connection established with client.")

    while True:
        # already re-ordered and buffered by the api
        data = server_sock.recv() 
        
        if not data:
            # If recv() returns None or empty, menas the client disconnected
            print("Client disconnected.")
            break
        
        print(f"Server received: {data.decode()}")

        server_sock.send(b'Message received!', isReliable=True)

except KeyboardInterrupt:
    print("Shutting down server.")

finally:
    server_sock.close()