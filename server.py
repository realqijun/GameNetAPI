from GamePacketHeader import GamePacketHeader
from GameNetAPI import GameNetAPI




def main():
    api = GameNetAPI()
    api.bind('127.0.0.1', SERVER_PORT)
    api.listen()
    while True:
        data = api.recv()
        print(data.decode(encoding="utf-8"))

    # parse header

    # handle reliable packet: easy, just bring it to application and send ACK

    # handle unreliable packet:
        # buffer packets based on sequence number, might need to reorder
        # deliver packets to application based on sequence number



    


    # measure performance: latency (RTT), jitter, throughput, packet delivery ratio
    # Print logs showing SeqNo, ChannelType, Timestamp, retransmissions, packet arrivals and RTT

main()

# --- Example Usage ---
if __name__ == "__main__":
    print(f"--- Game Packet Header Protocol ---")
    print(f"Header size: {HEADER_SIZE} bytes")

    # 1. CREATE A HEADER (e.g., a SYN packet for a reliable channel)
    # Using a high-resolution timestamp (e.g., in nanoseconds)
    import time
    
    header_to_send = GamePacketHeader(
        timestamp=time.time_ns(),
        sequence_num=100,
        ack_num=0,
        checksum=0,      # Checksum would be calculated *after* packing
        is_reliable=True,
        is_ack=False,
        is_syn=True,
        is_fin=False
    )
    
    print(f"\n[1] Header object to send:\n{header_to_send}")

    # 2. PACK THE HEADER
    try:
        packed_bytes = header_to_send.pack()
        print(f"\n[2] Packed header as bytes:\n{packed_bytes.hex()} ({len(packed_bytes)} bytes)")
        
        # TODO: Calculate checksum over (header + payload)
        # and re-pack with the correct checksum.
        # For now, we'll use the 0-checksum packet.

    except struct.error as e:
        print(f"Failed to pack: {e}")
        exit()
        
    # --- SIMULATE SENDING/RECEIVING ---
    # (Imagine these bytes are sent over UDP)
    
    # 3. ADD A PAYLOAD
    payload = b'{"player_id": 1, "action": "JUMP"}'
    full_packet = packed_bytes + payload
    
    print(f"\n[3] Full packet (Header + Payload) to send:\n{full_packet.hex()}")

    # --- AT THE RECEIVER ---
    
    print("\n--- Receiver Side ---")
    
    # 4. PARSE THE FULL PACKET
    try:
        # Get just the header bytes from the start of the packet
        received_header_bytes = full_packet[:HEADER_SIZE]
        
        # Get the payload
        received_payload = full_packet[HEADER_SIZE:]
        
        # Unpack the header bytes into an object
        parsed_header = GamePacketHeader.unpack(received_header_bytes)
        
        print(f"\n[4] Parsed header object:\n{parsed_header}")
        print(f"     Parsed payload:\n{received_payload.decode('utf-8')}")

        # 5. GET THE DICTIONARY (as you requested)
        header_dict = parsed_header.to_dict()
        print(f"\n[5] Header as a dictionary:\n{header_dict}")
        
        # You can now easily access fields
        if header_dict['is_reliable']:
            print("     This is a RELIABLE packet.")
            
    except ValueError as e:
        print(f"Error parsing packet: {e}")