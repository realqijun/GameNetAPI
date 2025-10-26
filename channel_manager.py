import time

RELIABLE = 0
UNRELIABLE = 1
SKIP_THRESHOLD_MS = 200  # Time to wait before skipping HOL packet

class ReliableChannelManager:
    # Selective Repeat/Go-Back-N implementation simplified
    def __init__(self):
        # Sender side: {SeqNo: {'data': packet_bytes, 'ts': last_sent_time, 'addr': remote_addr}}
        self.send_buffer = {} 
        
        # Receiver side: {SeqNo: {'packet': parsed_packet, 'arrival_ts': time}}
        self.receive_buffer = {}
        self.expected_seq_num = 0
        self.last_hol_arrival_ts = 0 # Timestamp of the first received packet when HOL was missing

    # --- Sender Logic ---
    def buffer_and_schedule(self, packet_bytes, seq_num, remote_addr):
        # Timestamp is for the *first* send time
        self.send_buffer[seq_num] = {
            'data': packet_bytes, 
            'ts': int(time.time() * 1000), 
            'addr': remote_addr,
            'last_sent_ts': int(time.time() * 1000)
        }

    def ack_received(self, seq_num):
        if seq_num in self.send_buffer:
            del self.send_buffer[seq_num]
            return True
        return False

    def get_retransmit_list(self, now_ms, timeout_ms):
        retransmit_list = []
        for seq_num, item in self.send_buffer.items():
            if now_ms - item['last_sent_ts'] > timeout_ms:
                item['last_sent_ts'] = now_ms # Update last sent time
                retransmit_list.append((seq_num, item['data'], item['addr']))
        return retransmit_list

    # --- Receiver Logic (Part e) ---
    def receive_packet(self, packet, callback, now_ms):
        seq = packet['seq']
        
        # 1. Buffer the packet
        if seq not in self.receive_buffer:
            self.receive_buffer[seq] = {'packet': packet, 'arrival_ts': now_ms}
            
        # If the expected packet is missing, and this is the first out-of-order packet,
        # start the timeout clock for the Head-of-Line (HOL) packet.
        if seq > self.expected_seq_num and self.expected_seq_num not in self.receive_buffer:
            if self.last_hol_arrival_ts == 0:
                self.last_hol_arrival_ts = now_ms
                
        # 2. Check for in-order delivery
        self._deliver_in_order(callback, now_ms)

    def _deliver_in_order(self, callback, now_ms):
        delivered = False
        
        # Check HOL Skip Threshold (Part e)
        if self.expected_seq_num not in self.receive_buffer and self.last_hol_arrival_ts != 0:
            time_waiting = now_ms - self.last_hol_arrival_ts
            if time_waiting >= SKIP_THRESHOLD_MS:
                print(f"SKIP TIMEOUT: Skipping Seq={self.expected_seq_num}. Waited {time_waiting}ms.")
                # Increment expected seq num to skip the lost packet
                self.expected_seq_num = (self.expected_seq_num + 1) % 65536
                self.last_hol_arrival_ts = 0 # Reset HOL timer
                delivered = True # Force re-check of delivery loop

        # Deliver contiguous packets
        while self.expected_seq_num in self.receive_buffer:
            packet_info = self.receive_buffer.pop(self.expected_seq_num)
            packet = packet_info['packet']
            self.last_hol_arrival_ts = 0 # Reset HOL timer upon successful delivery
            
            latency = now_ms - packet['ts']
            self.expected_seq_num = (self.expected_seq_num + 1) % 65536
            callback(packet['payload'], RELIABLE, packet['seq'], latency)
            print(f"PACKET DELIVERED (R): Seq={packet['seq']}, Latency={latency}ms")
            delivered = True
            
        return delivered