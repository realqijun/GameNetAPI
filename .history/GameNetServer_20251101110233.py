import socket
import time
import threading
from collections import deque
# This import depends on your 'header_protocol.py' file
from header_protocol import GamePacketHeader, HEADER_SIZE

# This class IS your gameNetAPI (Receiver Side)
class GameNetAPI_Receiver:
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False
        self.server_thread = None

        # --- State Management ---
        # Stores out-of-order packets: {seq_num: payload}
        self.reliable_buffer = {} 
        # The next seq_num we expect to deliver to the app
        self.next_expected_seq = 0 
        # Client address (simplified for one client)
        self.client_addr = None 

        # --- Public Queue ---
        # This is where we put the final, ordered data for the
        # Receiver Application to consume.
        self.application_queue = deque()

    def start(self):
        """Starts the server listener in a new thread."""
        try:
            self.sock.bind((self.host, self.port))
        except OSError as e:
            print(f"Failed to bind to {self.host}:{self.port}. Error: {e}")
            print("Is the port already in use?")
            return

        self.running = True
        # The listener runs in a separate thread
        # 'daemon=True' means the thread will exit when the main app exits
        self.server_thread = threading.Thread(target=self._listen, daemon=True)
        self.server_thread.start()
        print(f"Server API started listening on {self.host}:{self.port}")

    def stop(self):
        """Stops the server."""
        self.running = False
        # Unblock the sock.recvfrom() call
        self.sock.close() 
        if self.server_thread:
            self.server_thread.join()
        print("Server API stopped.")

    def _listen(self):
        """
        The private main loop that listens for packets.
        This runs in its own thread.
        """
        while self.running:
            try:
                # 1. RECEIVE A PACKET
                data, addr = self.sock.recvfrom(1024) # 1024 = buffer size
                
                # Store client address to send ACKs back
                if not self.client_addr:
                    self.client_addr = addr

                # 2. PARSE THE HEADER
                if len(data) < HEADER_SIZE:
                    print(f"Ignoring runt packet from {addr}")
                    continue
                
                header_bytes = data[:HEADER_SIZE]
                payload = data[HEADER_SIZE:]
                
                # We USE the header class to parse
                header = GamePacketHeader.unpack(header_bytes)
                
                # TODO: Verify checksum here

                # 3. PROCESS THE PACKET
                self._process_packet(header, payload, addr)

            except socket.error as e:
                # This error is expected when self.sock.close() is called
                if not self.running:
                    break 
                print(f"Socket error: {e}")
            except Exception as e:
                print(f"Error processing packet: {e}")

    def _process_packet(self, header, payload, addr):
        """
        Internal logic to decide what to do with a packet.
        """
        # Handle SYN (connection logic)
        if header.is_syn and not header.is_ack:
            print(f"Received SYN from {addr}. Sending SYN-ACK.")
            # Set initial sequence number based on client's first seq num
            self.next_expected_seq = header.sequence_num
            self._send_syn_ack(addr, header.sequence_num)
            return

        # Handle reliable data packets
        if header.is_reliable:
            self._handle_reliable(header, payload, addr)
        else:
            # Handle unreliable data packets
            self._handle_unreliable(header, payload, addr)

    def _handle_reliable(self, header, payload, addr):
        """
        Implements RDT logic (buffering, reordering, ACKing).
        """
        # --- 1. Send an ACK ---
        # (Using Selective Repeat logic: ACK every received packet)
        self._send_ack(addr, header.sequence_num)

        # --- 2. Check Sequence Number ---
        if header.sequence_num == self.next_expected_seq:
            # This is the exact packet we were waiting for.
            
            # Deliver it to the application
            self.application_queue.append(payload)
            self.next_expected_seq += 1
            
            # Now, check the buffer for any subsequent packets
            # that we can now also deliver
            while self.next_expected_seq in self.reliable_buffer:
                buffered_payload = self.reliable_buffer.pop(self.next_expected_seq)
                self.application_queue.append(buffered_payload)
                self.next_expected_seq += 1

        elif header.sequence_num > self.next_expected_seq:
            # It's an out-of-order packet (in the future). Buffer it.
            if header.sequence_num not in self.reliable_buffer:
                print(f"Buffering out-of-order packet: {header.sequence_num}")
                self.reliable_buffer[header.sequence_num] = payload
            else:
                print(f"Already buffered packet: {header.sequence_num}")

        else:
            # It's a duplicate of a packet we've already processed
            # (seq_num < self.next_expected_seq).
            # The ACK we sent must have been lost.
            # We already sent an ACK (step 1), so we're done.
            print(f"Received duplicate old packet: {header.sequence_num}")

    def _handle_unreliable(self, header, payload, addr):
        """
        No buffering, no reordering. Just deliver it.
        """
        self.application_queue.append(payload)

    def _send_ack(self, addr, ack_num):
        """Helper method to create and send an ACK packet."""
        ack_header = GamePacketHeader(
            timestamp=time.time_ns(),
            sequence_num=0, # ACKs might not need their own seq num
            ack_num=ack_num, # Acknowledge the packet we received
            checksum=0,      # TODO: Calculate checksum
            is_reliable=True, # ACKs are part of the reliable channel
            is_ack=True,
            is_syn=False,
            is_fin=False
        )
        packet = ack_header.pack()
        self.sock.sendto(packet, addr)

    def _send_syn_ack(self, addr, ack_num):
        """Helper method to create and send a SYN-ACK packet."""
        syn_ack_header = GamePacketHeader(
            timestamp=time.time_ns(),
            sequence_num=0, # Server's initial sequence number
            ack_num=ack_num, # Acknowledge the client's SYN
            checksum=0,      # TODO: Calculate checksum
            is_reliable=True,
            is_ack=True,
            is_syn=True,
            is_fin=False
        )
        packet = syn_ack_header.pack()
        self.sock.sendto(packet, addr)

    # --- Public API Method ---
    def get_application_packet(self):
        """
        This is the public method the Receiver Application calls
        to get the next available, processed packet payload.
        
        Returns:
            bytes: The packet payload, or None if no packet is available.
        """
        if self.application_queue:
            # 'popleft' is First-In, First-Out (FIFO)
            return self.application_queue.popleft()
        return None