# GameNetAPI

## Project Overview
GameNetAPI is a custom transport layer protocol built over a single UDP socket to support two distinct logical channels: Reliable (for critical game state/commands) and Unreliable (for non-critical, time-sensitive data like position updates). This design is optimized for low-latency, real-time applications such as online gaming. GameNetAPI handles all connection management, packet construction, demultiplexing, and the Reliable Data Transfer (RDT) logic.

## Protocol and RDT Details
Packet Header Format
All H-UDP packets share a 20-byte header:
| Field Name | Size (Bytes) | Description |
| ---------- | ------------ | ----------- |
| Timestamp | 8 | Time in milliseconds when the packet was created. |
| SeqNo | 4 | Packet sequence number (for unreliable channel, the seqno is always -1) |
| AckNo | 4 | Packet ACK number (for reliable channel) |
| Checksum | 2 | 1's complement checksum of the header with checksum field set to 0 |
| Packet flags | 2 | First bit is used for packet reliability, other bits are used set what type of packet it is (e.g. FIN, ACK, SYN, RST) |
| Payload | Variable | Application data |

Reliable Channel Logic
- Algorithm: Selective Repeat.
- Retransmission: Packets are retransmitted if no ACK is received within 50 ms.
- In-Order Delivery & Skip Timeout: The receiver buffers and reorders reliable packets. If the Head-of-Line (HOL) packet is lost and the wait time exceeds 200 ms threashold, the missing packet is skipped to prevent indefinite HOL blocking, allowing subsequent in-order packets to be delivered.

## Setup and Execution
Prerequisites
1. Python 3.10 and above
