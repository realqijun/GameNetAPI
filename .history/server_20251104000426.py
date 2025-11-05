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
        # 5. This one call is your "get_application_packet()"
        #    - It blocks and waits for the API to give it data
        #    - It's guaranteed to be in-order
        #    - It's guaranteed to be from the reliable stream
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