import sys
from api.gns import GameNetSocket

SERVER_ADDR = ('127.0.0.1', 6767)

def run_server():
    server = GameNetSocket()
    server.bind(SERVER_ADDR)
    server.listen()

    print(f"[Server] Listening on {SERVER_ADDR}...")
    server.accept()
    print("[Server] Client connection accepted.")

    try:
        while True:
            print("[Server] Waiting for test command...")
            cmd_data = server.recv()
            if not cmd_data:
                break
            
            command = cmd_data.decode('utf-8')
            print(f"[Server] Received command: {command}")

            if command == "TEST_INTEGRITY":
                # Echo everything back reliably
                print("[Server] Running: TEST_INTEGRITY")
                while True:
                    data = server.recv()
                    if data == b'INTEGRITY_DONE':
                        server.send(b'INTEGRITY_OK', True)
                        break
                    server.send(data, True) # Echo back reliably
                print("[Server] Finished: TEST_INTEGRITY")
                
            elif command == "TEST_RTT":
                # Echo pings
                print("[Server] Running: TEST_RTT")
                for _ in range(20): # Expect 20 pings
                    data = server.recv()
                    server.send(data, True) # Echo back 'PING' as 'PONG'
                print("[Server] Finished: TEST_RTT")

            elif command == "TEST_THROUGHPUT":
                # Act as a data sink and echo final packet
                print("[Server] Running: TEST_THROUGHPUT")
                while True:
                    data = server.recv()
                    if data == b'THROUGHPUT_DONE':
                        server.send(b'THROUGHPUT_OK', True) # Final ack
                        break
                print("[Server] Finished: TEST_THROUGHPUT")

            elif command == "TEST_UNRELIABLE":
                # Count unreliable packets
                print("[Server] Running: TEST_UNRELIABLE")
                count = 0
                total = 1000 # Client will send 1000
                server.context.sock.settimeout(2.0) # Set 2 sec timeout
                
                try:
                    for _ in range(total):
                        data = server.recv()
                        if data == b'UNRELIABLE_PING':
                            count += 1
                except Exception as e:
                    # This is expected, client stops sending
                    print(f"[Server] Timeout waiting for unreliable packets.")
                
                server.context.sock.settimeout(None) # Clear timeout
                
                # Send the result back reliably
                result_msg = f"COUNT:{count}".encode('utf-8')
                server.send(result_msg, True)
                print(f"[Server] Finished: TEST_UNRELIABLE (Counted {count})")
            
            elif command == "CLOSE":
                print("[Server] Client requested close.")
                break

    except Exception as e:
        print(f"[Server] Error: {e}", file=sys.stderr)
    finally:
        print("[Server] Closing server socket.")
        server.close()

if __name__ == "__main__":
    run_server()

