# This file is part of the blueprint package.
# Copyright (c) 2024 Arduino SA
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import opta
import time
import logging


if __name__ == "__main__":
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO
    )

    opta = opta.Opta(bus_id=3)

    # enum_devices initializes the bus, resets all expansions, and returns a list of
    # detected expansions. NOTE: keep a reference to the list of expansion for later
    # use, as every time this function is called it restarts the enumeration process.
    for e in opta.enum_devices():
        print("")
        logging.info(f"Expansion type: {e.type} address: 0x{e.addr:02X} name: {e.name}")

        # Read firmware version.
        major, minor, patch = e.firmware_version()
        logging.info(f"Firmware Version Major: {major} Minor: {minor} Patch: {patch}")

        # Read product ID.
        pid = e.product_id()
        logging.info("Product ID bytes: " + ", ".join(["0x%02X"%(a) for a in pid[0:8]]))

        if e.type == "digital":
            # Write digital pins. If the default state and timeout (in milliseconds) are
            # also specified, the pins will revert to the default state after the timeout.
            e.digital(pins=0b10101010, default=0b01010101, timeout=3000)

            # If no args are specified, digital() returns all digital pins.
            pins = e.digital()
            logging.info(f"Digital pins: 0b{pins:08b}")

            # Digital is also analog \../
            logging.info("Analog pin  [0   ]: %d" % e.analog(channel=0))
            logging.info("Analog pins [0..7]: " + str(e.analog()))

        if e.type == "analog":
            # Configure the first channel as DAC. Only channel type and channel mode are
            # requried, all other args have reasonable defaults, that depend on the mode.
            e.analog(channel=0, channel_type="dac", channel_mode="voltage", value=7540)

            # Configure the second channel as ADC. Only channel type and channel mode are
            # requried, all other args have reasonable defaults, that depend on the mode.
            e.analog(channel=1, channel_type="adc", channel_mode="voltage", pulldown=True,
                     rejection=False, diagnostic=False, average=0, secondary=False)
            
            # Read analog channel.
            # If channel 1 is connect to channel 2 this should print 65535.
            logging.info("ADC channel  [0   ]: %d" % e.analog(channel=1))
            logging.info("ADC channels [0..7]: " + str(e.analog()))

            # Configure the third channel as RTD. Only channel type and channel mode are
            # requried, all other args have reasonable defaults, that depend on the mode.
            e.analog(channel=2, channel_type="rtd", use_3_wire=True, current_ma=10)
            logging.info("RTD channel  [1   ]: %d" % e.analog(channel=2))
