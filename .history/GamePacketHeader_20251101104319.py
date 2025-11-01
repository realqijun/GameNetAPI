import struct
from dataclasses import dataclass, asdict

# --- 1. Header Constants ---

# We group all bit-fields (flags) into a single 1-byte (8-bit) field.
# This is the 'format string' for the 'struct' module.
#
#   ! = Network Byte Order (Big-Endian)
#   Q = Timestamp (unsigned long long, 8 bytes / 64 bits)
#   I = Sequence Number (unsigned int, 4 bytes / 32 bits)
#   I = Ack Number (unsigned int, 4 bytes / 32 bits)
#   H = Checksum (unsigned short, 2 bytes / 16 bits)
#   B = Flags (unsigned char, 1 byte / 8 bits)
#
# Total Header Size: 8 + 4 + 4 + 2 + 1 = 19 bytes
HEADER_FORMAT_STRING = '!QIIHB'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT_STRING)

# --- 2. Bit-field Masks ---
# We use these bitmasks to set or read our 1-bit flags
# from the 1-byte 'flags' field.
#
#   Bit 3 (0000 1000) = Channel Type (1=Reliable, 0=Unreliable)
#   Bit 2 (0000 0100) = ACK flag
#   Bit 1 (0000 0010) = SYN flag
#   Bit 0 (0000 0001) = FIN flag
# (Bits 7-4 are reserved)
CHANNEL_TYPE_MASK = 0b00001000  # 0x08
ACK_MASK          = 0b00000100  # 0x04
SYN_MASK          = 0b00000010  # 0x02
FIN_MASK          = 0b00000001  # 0x01


@dataclass
class GamePacketHeader:
    """
    A dataclass to represent our custom packet header.
    Provides methods to pack into bytes and unpack from bytes.
    """
    timestamp: int
    sequence_num: int
    ack_num: int
    checksum: int
    
    # Flags as easy-to-use booleans
    is_reliable: bool  # This is your 'Channel Type'
    is_ack: bool       # This is your 'ACK' flag
    is_syn: bool       # This is your 'SYN' flag
    is_fin: bool       # This is your 'FIN' flag

    # is for defensive measures so that the types will be correct format, init fxn has alr been written for me
    def __post_init__(self):
        self.timestamp = int(self.timestamp)
        self.sequence_num = int(self.sequence_num)
        self.ack_num = int(self.ack_num)
        self.checksum = int(self.checksum)

    def pack(self) -> bytes:
        """
S        erializes the header object into a 19-byte bytestring.
        """
        # 1. Assemble the 1-byte 'flags' field from booleans
        flags = 0
        if self.is_reliable:
            flags |= CHANNEL_TYPE_MASK
        if self.is_ack:
            flags |= ACK_MASK
        if self.is_syn:
            flags |= SYN_MASK
        if self.is_fin:
            flags |= FIN_MASK
        
        # 2. Pack all fields into bytes
        try:
            return struct.pack(
                HEADER_FORMAT_STRING,
                self.timestamp,
                self.sequence_num,
                self.ack_num,
                self.checksum,
                flags
            )
        except struct.error as e:
            print(f"Error packing header: {e}")
            print(f"Header data: {self}")
            # Re-raise for the caller to handle
            raise

    @classmethod
    def unpack(cls, data: bytes) -> 'GamePacketHeader':
        """
        Parses 19 bytes of data and returns a GamePacketHeader object.
        """
        if len(data) < HEADER_SIZE:
            raise ValueError(f"Need {HEADER_SIZE} bytes to unpack header, but got {len(data)}")

        # 1. Unpack the raw bytes into a tuple
        unpacked_tuple = struct.unpack(HEADER_FORMAT_STRING, data[:HEADER_SIZE])
        
        timestamp, sequence_num, ack_num, checksum, flags = unpacked_tuple
        
        # 2. Decode the 1-byte 'flags' field into booleans
        is_reliable = (flags & CHANNEL_TYPE_MASK) > 0
        is_ack       = (flags & ACK_MASK) > 0
        is_syn       = (flags & SYN_MASK) > 0
        is_fin       = (flags & FIN_MASK) > 0
        
        # 3. Create and return the object
        return cls(
            timestamp=timestamp,
            sequence_num=sequence_num,
            ack_num=ack_num,
            checksum=checksum,
            is_reliable=is_reliable,
            is_ack=is_ack,
            is_syn=is_syn,
            is_fin=is_fin
        )
    
    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the header.
        This is the method you requested.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data_dict: dict) -> 'GamePacketHeader':
        """
        Helper method to create a header object from a dictionary.
        """
        return cls(**data_dict)


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

