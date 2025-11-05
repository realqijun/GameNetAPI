import sys
import time
import os
from api.gns import GameNetSocket

SERVER_ADDR = ('127.0.0.1', 6767)
CLIENT_ADDR = ('127.0.0.1', 4896)

def test_data_integrity(sock: GameNetSocket, test_data: bytes):
    print("--- 1. Running Data Integrity Test ---")
    sock.send(b'TEST_INTEGRITY', True)

    chunk_size = 1400

    print(f"Sending {len(test_data)} bytes in {len(test_data)//chunk_size} chunks...")

    sent_data = b''
    for i in range(0, len(test_data), chunk_size):
        chunk = test_data[i:i+chunk_size]
        sock.send(chunk, True)
        sent_data += chunk

    sock.send(b'INTEGRITY_DONE', True)

    print("All data sent. Waiting for echoed data...")

    received_data = b''
    while True:
        data = sock.recv()
        if data == b'INTEGRITY_OK':
            break
        received_data += data

    print(f"Total Sent:     {len(sent_data)} bytes")
    print(f"Total Received: {len(received_data)} bytes")

    assert sent_data == received_data, "Data mismatch!"
    assert len(sent_data) == len(test_data), "Sent data length mismatch!"
    assert len(received_data) == len(test_data), "Received data length mismatch!"

    print("--- Data Integrity Test: PASSED ---")

def test_rtt(sock: GameNetSocket):
    print("--- 2. Running RTT Test ---")
    sock.send(b'TEST_RTT', True)

    rtt_list = []
    for i in range(20):
        time.sleep(0.1) # Small delay to not flood

        start_time = time.monotonic()
        sock.send(b'PING', True)
        data = sock.recv()
        end_time = time.monotonic()

        if data == b'PING':
            rtt = (end_time - start_time) * 1000
            rtt_list.append(rtt)
            print(f"Ping {i+1}/20: RTT = {rtt:.2f} ms")
        else:
            print(f"Ping {i+1}/20: FAILED (Bad Response: {data})")

    if not rtt_list:
        print("--- RTT Test: FAILED (No responses) ---")
        raise RuntimeError("RTT Test Failed")

    min_rtt = min(rtt_list)
    avg_rtt = sum(rtt_list) / len(rtt_list)
    max_rtt = max(rtt_list)

    print(f"\n--- RTT Stats ---")
    print(f"Min: {min_rtt:.2f} ms")
    print(f"Avg: {avg_rtt:.2f} ms")
    print(f"Max: {max_rtt:.2f} ms")
    print("--- RTT Test: COMPLETED ---")

def test_throughput(sock: GameNetSocket):
    print("--- 3. Running Throughput Test ---")
    sock.send(b'TEST_THROUGHPUT', True)

    data_size_mb = 5
    total_data_size = data_size_mb * 1024 * 1024
    chunk = os.urandom(1400)
    num_chunks = total_data_size // len(chunk)

    print(f"Sending {data_size_mb} MB of data...")
    start_time = time.monotonic()

    for i in range(num_chunks):
        sock.send(chunk, True)

    sock.send(b'THROUGHPUT_DONE', True)

    # Wait for server to ack all data
    ack = sock.recv()
    assert ack == b'THROUGHPUT_OK', "Throughput test ACK failed"

    end_time = time.monotonic()
    duration = end_time - start_time
    throughput_mbps = (total_data_size * 8) / duration / 1_000_000

    print(f"\n--- Throughput Stats ---")
    print(f"Sent {total_data_size / 1024 / 1024:.2f} MB in {duration:.2f} seconds")
    print(f"Throughput: {throughput_mbps:.2f} Mbps")
    print("--- Throughput Test: COMPLETED ---")

def test_unreliable(sock: GameNetSocket):
    print("--- 4. Running Unreliable Send Test ---")
    sock.send(b'TEST_UNRELIABLE', True)

    total_to_send = 1000
    print(f"Sending {total_to_send} unreliable packets...")

    for _ in range(total_to_send):
        sock.send(b'UNRELIABLE_PING', False) # isReliable=False
        time.sleep(0.001) # 1ms gap

    print("All packets sent. Waiting for server count...")

    # Server sends the result back reliably
    result_data = sock.recv()
    result = result_data.decode('utf-8')

    if result.startswith("COUNT:"):
        count = int(result.split(':')[1])
        loss = 100 - (count / total_to_send * 100)
        print(f"\n--- Unreliable Stats ---")
        print(f"Server received {count}/{total_to_send} packets")
        print(f"Packet Loss: {loss:.1f}%")
        print("--- Unreliable Test: COMPLETED ---")
    else:
        print(f"--- Unreliable Test: FAILED (Bad response: {result}) ---")
        raise RuntimeError("Unreliable Test Failed")

def run_client():
    sock = GameNetSocket()
    sock.bind(CLIENT_ADDR)
    print(f"[Client] Connecting to {SERVER_ADDR}...")

    with open('tests/test_cases/1.txt', 'rb') as f:
        test_data = f.read()

    try:
        sock.connect(SERVER_ADDR)
        print("[Client] Connected to server.")

        # --- Run all tests ---
        test_data_integrity(sock, test_data)
        test_rtt(sock)
        test_throughput(sock)
        test_unreliable(sock)

        print("[Client] All tests done. Closing connection.")
        sock.send(b'CLOSE', True)

    except Exception as e:
        print(f"\n--- TEST FAILED ---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sock.close()
        sys.exit(1)

    finally:
        sock.close()

if __name__ == "__main__":
    run_client()

