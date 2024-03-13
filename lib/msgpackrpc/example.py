# This file is part of the msgpack-rpc module.
# Any copyright is dedicated to the Public Domain.
# https://creativecommons.org/publicdomain/zero/1.0/

import time
import logging
import msgpackrpc
import gc


class Adder:
    def __init__(self):
        pass

    def add(self, a, b):
        logging.info(f"add({a}, {b}) is called")
        return a + b


def sub(a, b):
    logging.info(f"sub({a}, {b}) is called")
    return a - b


if __name__ == "__main__":
    # Configure the logger.
    # All message equal to or higher than the logger level are printed.
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO,
    )

    # Create an RPC object
    rpc = msgpackrpc.MsgPackRPC()

    # Register objects or functions to be called by the remote processor.
    rpc.bind(Adder())
    rpc.bind(sub)

    # Start the remote processor and wait for it to be ready to communicate.
    rpc.start(firmware=0x08180000, timeout=1000, num_channels=2)

    while True:
        alloc = gc.mem_alloc()
        # Async calls
        f1 = rpc.call_async("add", 0, 1)
        f2 = rpc.call_async("add", 0, 2)
        f3 = rpc.call_async("add", 0, 3)

        # Can join async call in any order
        logging.info("async add(0, 3) => %d", f3.join())

        # Sync call
        res = rpc.call("add", 2, 2)
        logging.info("sync add(2, 2) => %d" % res)
        logging.info("async add(0, 1) => %d" % f1.join())
        logging.info("async add(0, 2) => %d" % f2.join())
        logging.info("memory per iteration %d" % (gc.mem_alloc() - alloc))
        time.sleep_ms(250)
