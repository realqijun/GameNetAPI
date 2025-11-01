

def


def main():
    api = GameNetAPI()
    api.bind('127.0.0.1', SERVER_PORT)
    api.listen()
    while True:
        data = api.recv()
        print(data.decode(encoding="utf-8"))

    # parse header

        # handle reliable packet

        # handle unreliable packet

    


    # measure performance: latency (RTT), jitter, throughput, packet delivery ratio
    # Print logs
showing SeqNo, ChannelType, Timestamp, retransmissions, packet arrivals and
RTT,
main()