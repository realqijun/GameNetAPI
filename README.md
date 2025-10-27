# GameNetAPI

## Project Overview
GameNetAPI is a custom transport layer protocol built over a single UDP socket to support two distinct logical channels: Reliable (for critical game state/commands) and Unreliable (for non-critical, time-sensitive data like position updates). This design is optimized for low-latency, real-time applications such as online gaming. GameNetAPI handles all connection management, packet construction, demultiplexing, and the Reliable Data Transfer (RDT) logic.

## Protocol and RDT Details
Packet Header Format
All H-UDP packets share a 7-byte header:
| Field Name | Size (Bits) | Description |
| ---------- | ------------ | ----------- |
| ChannelType | 1 | 0 = Data (Reliable), 1 = Data (Unreliable), 2 = ACK | 
| SeqNo | 32 | Packet sequence number (for reliable channel and ACKs) |
| Timestamp | 64 | Sender's time of transmission (milliseconds) |
| Checksum | 16 | 1's complement checksum of the header with checksum field set to 0 |
| Payload | Variable | Application data |

Reliable Channel Logic
- Algorithm: Selective Repeat.
- Retransmission: Packets are retransmitted if no ACK is received within 50 ms.
- In-Order Delivery & Skip Timeout: The receiver buffers and reorders reliable packets. If the Head-of-Line (HOL) packet is lost and the wait time exceeds 200 ms threashold, the missing packet is skipped to prevent indefinite HOL blocking, allowing subsequent in-order packets to be delivered.

## Setup and Execution
Prerequisites
1. Python 3.9 and above
