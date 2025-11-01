from dataclasses import dataclass,

@dataclass



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