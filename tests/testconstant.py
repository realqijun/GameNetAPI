from api.states.gnssterminated import GNSStateTerminated
from time import sleep

TEST_DURATION = 30
TARGET_RATE = 100


def busy_wait_till_terminate(sock):
    while not isinstance(sock.state, GNSStateTerminated):
        continue
    sleep(1)
