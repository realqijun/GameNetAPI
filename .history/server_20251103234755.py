# You no longer need your GameNetAPI_Receiver.py file.
# You just import the API we discussed.
from gamenetsocket import GameNetSocket 

# 1. Create the socket
server_sock = GameNetSocket()

try:
    # 2. Bind, Listen, and Accept
    server_sock.bind(('0.0.0.0', 12345))
    server_sock.listen()
    
    print("Server is waiting for a connection...")
    
    # 3. This one call handles EVERYTHING:
    #    - It waits for a SYN
    #    - It handles the SYN-ACK
    #    - It waits for the final ACK
    #    - It starts all the worker threads
    #    - It blocks your main thread until it's all done
    server_sock.accept() 
    
    print("A client has connected!")

    # 4. Run your main server loop
    while True:
        # 5. This one call is your "get_application_packet()"
        #    - It blocks and waits for the API to give it data
        #    - It's guaranteed to be in-order
        #    - It's guaranteed to be from the reliable stream
        data = server_sock.recv() 
        
        if not data:
            # If recv() returns None or empty, the client disconnected
            print("Client disconnected.")
            break
            
        # 6. You are now free to just use the data.
        #    No threads, no buffers, no sequence numbers to check.
        print(f"Server received: {data.decode()}")

        # You can also send data back!
        server_sock.send(b'Message received!', isReliable=True)

except KeyboardInterrupt:
    print("Shutting down server.")
finally:
    # 7. Cleanly close the connection
    server_sock.close() # This handles the 4-way FIN handshake