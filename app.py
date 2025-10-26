import random
import time
from hudp import HUDPBase, RELIABLE, UNRELIABLE

# --- Receiver Application ---
def receiver_application_callback(data, channel_type, seq_num, latency):
    # This is where the application logic receives the data from the API
    channel = "RELIABLE" if channel_type == RELIABLE else "UNRELIABLE"
    print(f"  APP RECEIVE: {channel} Seq={seq_num}, Data='{data}', Latency={latency}ms")

def run_receiver(port, duration):
    api = HUDPBase(port)
    start_time = time.time()
    
    while time.time() - start_time < duration:
        api.poll_packets(receiver_application_callback)
        time.sleep(0.001) # Small sleep to avoid hogging CPU

    print("\n--- Receiver Metrics ---")
    print(api.get_metrics(duration))

# --- Sender Application ---
def run_sender(remote_addr, remote_port, rate_pps, duration):
    api = HUDPBase(random.randint(50000, 60000))
    target = (remote_addr, remote_port)
    
    start_time = time.time()
    packet_interval = 1.0 / rate_pps
    
    while time.time() - start_time < duration:
        is_reliable = random.choice([True, False]) # Randomly tag data (Part f)
        data = f"Packet from Sender {int(time.time() * 1000)}"
        
        api.send_data(target, data.encode(), is_reliable)
        
        # Handle incoming ACKs/Packets briefly
        api.poll_packets(lambda *args: None) # Sender ignores application data, only handles ACKs
        
        time.sleep(packet_interval - (time.time() - start_time) % packet_interval)
        
    print("\n--- Sender Metrics ---")
    print(api.get_metrics(duration))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python app.py [sender|receiver] [args...]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == "receiver":
        if len(sys.argv) != 4:
            print("Usage: python app.py receiver [port] [duration_sec]")
            sys.exit(1)
        port = int(sys.argv[2])
        duration = int(sys.argv[3])
        run_receiver(port, duration)
        
    elif mode == "sender":
        if len(sys.argv) != 6:
            print("Usage: python app.py sender [remote_addr] [remote_port] [rate_pps] [duration_sec]")
            sys.exit(1)
        remote_addr = sys.argv[2]
        remote_port = int(sys.argv[3])
        rate_pps = int(sys.argv[4])
        duration = int(sys.argv[5])
        run_sender(remote_addr, remote_port, rate_pps, duration)
        
    else:
        print("Invalid mode. Use 'sender' or 'receiver'.")
        sys.exit(1)