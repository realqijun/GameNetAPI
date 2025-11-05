from api.gns import GameNetSocket
from common import SERVER_PORT, FORWARDER_PORT
from datetime import datetime
from hudp import HUDPPacket
import time

class PacketStats:
    def __init__(self):
        self.packets_received = 0
        self.retransmissions = 0
        self.start_time = time.time()

    def log_packet(self, packet):
        timestamp = datetime.fromtimestamp(packet.time / 1000).strftime("%M:%S:%f")[:-3]
        channel = "RELIABLE" if packet.isReliable() else "UNRELIABLE"
        print(f"[{timestamp}] SEQ={packet.seq} | {channel} | "
              f"RTT={time.time() * 1000 - packet.time:.2f}ms")

def main():
    try:
        sock = GameNetSocket()
        sock.bind(('127.0.0.1', SERVER_PORT))
        sock.connect(('127.0.0.1', FORWARDER_PORT))
        
        stats = PacketStats()

        while True:
            try:
                data = sock.recv()
                packet = HUDPPacket.fromBytes(data)
                stats.log_packet(packet)
            except KeyboardInterrupt:
                print("Server shutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

    finally:
        if sock:
            sock.close()

if __name__ == "__main__":
    main()