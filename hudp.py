import socket
import struct
import time
from channel_manager import ReliableChannelManager

# Constants
RELIABLE = 0
UNRELIABLE = 1
ACK = 2
SKIP_THRESHOLD_MS = 200
TIMEOUT_MS = 50  # Retransmission Timeout

class HUDPBase:
    def __init__(self, local_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', local_port))
        self.reliable_seq_num = 0
        self.reliable_channel = ReliableChannelManager()
        self.metrics = {'reliable': {'sent': 0, 'received': 0, 'rtt_sum': 0},
                        'unreliable': {'sent': 0, 'received': 0}}
        print(f"H-UDP API listening on port {local_port}")

    # --- Packet Serialization/Deserialization ---
    def _create_packet(self, channel_type, payload):
        # Header format: !BHL (1B Channel, 2B SeqNo, 8B Timestamp)
        if channel_type != ACK:
            seq = self.reliable_seq_num
            if channel_type == RELIABLE:
                self.reliable_seq_num = (self.reliable_seq_num + 1) % 65536
        else:
            # For ACK, SeqNo holds the ACKed number
            seq = payload['ack_seq']

        timestamp = int(time.time() * 1000) # Milliseconds
        print(timestamp)
        header = struct.pack('!BHq', channel_type, seq, timestamp)
        
        # If ACK, the payload is minimal (e.g., an empty byte string or just the header)
        if channel_type == ACK:
            packet = header
        else:
            packet = header + payload

        return packet, seq, timestamp

    def _parse_packet(self, data):
        if len(data) < 11: return None # Min header size
        header = data[:11]
        payload = data[11:]
        channel_type, seq_num, timestamp = struct.unpack('!BHq', header)
        
        return {'type': channel_type, 'seq': seq_num, 
                'ts': timestamp, 'payload': payload, 'raw': data}

    # --- Core API Method (Part b) ---
    def send_data(self, remote_addr, data, is_reliable):
        channel_type = RELIABLE if is_reliable else UNRELIABLE
        
        # 1. Create packet
        packet_bytes, seq_num, ts = self._create_packet(channel_type, data)
        
        # 2. Handle Reliable Channel Logic (Part e)
        if is_reliable:
            self.reliable_channel.buffer_and_schedule(packet_bytes, seq_num, remote_addr)
            self.metrics['reliable']['sent'] += 1
            print(f"SENT (R): Seq={seq_num}, TS={ts}, Size={len(packet_bytes)}")
        else:
            self.metrics['unreliable']['sent'] += 1
            print(f"SENT (U): Seq={seq_num}, TS={ts}, Size={len(packet_bytes)}")
            
        # 3. Send over UDP
        self.sock.sendto(packet_bytes, remote_addr)

    # --- Core API Method (Part c) ---
    def poll_packets(self, receiver_app_callback):
        # Handle retransmissions first
        self._check_retransmissions()
        
        try:
            # Non-blocking receive (adjust size as needed)
            data, addr = self.sock.recvfrom(2048) 
            parsed_packet = self._parse_packet(data)
            if not parsed_packet: return
            
            now_ms = int(time.time() * 1000)
            
            # Demultiplexing (Part c, 3.a.iii)
            if parsed_packet['type'] == ACK:
                self._handle_ack(parsed_packet, now_ms)
            elif parsed_packet['type'] == RELIABLE:
                self._handle_reliable(parsed_packet, addr, receiver_app_callback, now_ms)
            elif parsed_packet['type'] == UNRELIABLE:
                self._handle_unreliable(parsed_packet, receiver_app_callback, now_ms)
                
        except socket.error as e:
            # Usually means no packet available (EAGAIN/EWOULDBLOCK)
            pass
            
    # --- Internal Handlers ---
    def _handle_ack(self, packet, now_ms):
        acked_seq = packet['seq']
        rtt = now_ms - packet['ts'] # Simple RTT: ACK arrival - Packet Send TS
        
        if self.reliable_channel.ack_received(acked_seq):
            self.metrics['reliable']['rtt_sum'] += rtt
            print(f"ACK RECEIVED: Seq={acked_seq}, RTT={rtt}ms")

    def _handle_unreliable(self, packet, callback, now_ms):
        self.metrics['unreliable']['received'] += 1
        latency = now_ms - packet['ts']
        # Fix: Pass UNRELIABLE instead of RELIABLE
        callback(packet['payload'], UNRELIABLE, packet['seq'], latency) 
        print(f"PACKET RECEIVED (U): Seq={packet['seq']}, TS={packet['ts']}, Latency={latency}ms") # Added TS log

    def _handle_reliable(self, packet, remote_addr, callback, now_ms):
        # 1. Send ACK back immediately
        self._send_ack(packet['seq'], remote_addr)
        
        # 2. Buffer, reorder, and deliver in-order (Part c, e)
        self.reliable_channel.receive_packet(packet, callback, now_ms)

    # --- Retransmission Logic (Part e) ---
    def _check_retransmissions(self):
        # This function would be called periodically (e.g., in poll_packets)
        now_ms = int(time.time() * 1000)
        retransmit_list = self.reliable_channel.get_retransmit_list(now_ms, TIMEOUT_MS)
        
        for seq_num, packet_data, addr in retransmit_list:
            self.sock.sendto(packet_data, addr)
            print(f"RETRANSMIT: Seq={seq_num}")

    def _send_ack(self, ack_seq_num, remote_addr):
        # ACKs are sent unreliably
        ack_packet, _, _ = self._create_packet(ACK, {'ack_seq': ack_seq_num})
        self.sock.sendto(ack_packet, remote_addr)
        
        
    # --- Metrics (Part i) ---
    def get_metrics(self, duration_sec):
        # Simplified RTT, PDR, and Throughput calculation
        rel_r = self.metrics['reliable']['received']
        rel_s = self.metrics['reliable']['sent']
        unrel_r = self.metrics['unreliable']['received']
        unrel_s = self.metrics['unreliable']['sent']
        
        avg_rtt = self.metrics['reliable']['rtt_sum'] / rel_r if rel_r > 0 else 0
        pdr_rel = (rel_r / rel_s * 100) if rel_s > 0 else 0
        pdr_unrel = (unrel_r / unrel_s * 100) if unrel_s > 0 else 0
        
        # Jitter calculation (requires tracking delay variance - omitted for brevity, but tracked in full implementation)
        
        # Throughput (approximate total bytes / duration)
        # Note: Actual throughput needs byte counting in _create_packet
        
        return {
            'Reliable': {'PDR': pdr_rel, 'Avg_RTT': avg_rtt},
            'Unreliable': {'PDR': pdr_unrel}
        }