# This file is part of the blueprint package.
# Copyright (c) 2024 Arduino SA
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import struct
import logging
from time import sleep_ms
from machine import I2C
from machine import Pin
from micropython import const

_MIN_ADDRESS = const(0x0B)
_TMP_ADDRESS = const(0x0A)
_MAX_ADDRESS = const(0x0B + 0x0A)

_CMD_HDR_LEN = const(0x03)
_CMD_CRC_LEN = const(0x01)

_CMD_DIR_SET = const(0x01)
_CMD_DIR_GET = const(0x02)

# Command args are encoded as (direction, opcode, response length)
_CMD_CHIP_RESET         = const((_CMD_DIR_SET, 0x01, 0))
_CMD_SET_ADDRESS        = const((_CMD_DIR_SET, 0x02, 0))
_CMD_GET_ADDRESS        = const((_CMD_DIR_GET, 0x03, 2))

_CMD_GET_PRODUCT_ID     = const((_CMD_DIR_GET, 0x25, 33))
_CMD_GET_FW_VERSION     = const((_CMD_DIR_GET, 0x16, 3))

_CMD_SET_DIGITAL_PIN    = const((_CMD_DIR_SET, 0x06, 0))
_CMD_GET_DIGITAL_BUS    = const((_CMD_DIR_GET, 0x04, 2))
_CMD_SET_DIGITAL_DEF    = const((_CMD_DIR_SET, 0x08, 0))

_CMD_CFG_ANALOG_ADC     = const((_CMD_DIR_SET, 0x09, 0))
_CMD_CFG_ANALOG_DAC     = const((_CMD_DIR_SET, 0x0C, 0))
_CMD_CFG_ANALOG_RTD     = const((_CMD_DIR_SET, 0x0E, 0))
_CMD_SET_ANALOG_DAC     = const((_CMD_DIR_SET, 0x0D, 0))

_CMD_GET_ANALOG_OD_PIN  = const((_CMD_DIR_GET, 0x05, 2))
_CMD_GET_ANALOG_OD_BUS  = const((_CMD_DIR_GET, 0x07, 32))

_CMD_GET_ANALOG_OA_PIN  = const((_CMD_DIR_GET, 0x0A, 3))
_CMD_GET_ANALOG_OA_BUS  = const((_CMD_DIR_GET, 0x0B, 16))
_CMD_GET_ANALOG_OA_RTD  = const((_CMD_DIR_GET, 0x0F, 5))

class Expansion:
    def __init__(self, opta, etype, addr, name):
        self.opta = opta
        self.type = etype
        self.addr = addr
        self.name = name
        self.channels = {}

    def product_id(self):
        """
        Returns the product ID bytes of the expansion.
        """
        return self.opta._send_cmd(self.addr, _CMD_GET_PRODUCT_ID)

    def firmware_version(self):
        """
        Returns the firmware version of the expansion.
        """
        return self.opta._send_cmd(self.addr, _CMD_GET_FW_VERSION)

    def digital(self, pins=None, default=None, timeout=None):
        """
        Configures or reads digital pins.
    
        Parameters:
            - pins : Digital pins mask to set. If None, returns the state of the pins.
            - default : The default state to which the pins will revert to after the timeout expires.
            - timeout : The timeout in milliseconds, after which pins revert to the default state.
    
        Returns: The current state of the digital pins if reading, or None if setting the pins.
        """
        if pins is not None:
            self.opta._send_cmd(self.addr, _CMD_SET_DIGITAL_PIN, pins)
        if timeout is not None and default is not None:
            arg = struct.pack("<BH", default if default is not None else 0, timeout)
            return self.opta._send_cmd(self.addr, _CMD_SET_DIGITAL_DEF, arg)
        return struct.unpack("<H", self.opta._send_cmd(self.addr, _CMD_GET_DIGITAL_BUS))[0]

    def analog(self, channel=None, channel_type=None, channel_mode=None, value=None, **kwargs):
        """
        Configures, reads, or writes ADC and DAC channels.

        Parameters:
            - channel : The channel number to configure, read, or write. If None, reads all ADC channels.
            - channel_type : Channel type can be "adc" or "dac".
            - channel_mode : "voltage" (default for ADC channels) or "current".
            - value : Value to write to a DAC channel.

        kwargs :
            ADC configuration:
            - average : Number of points for moving average (0-255, default=0).
            - rejection : Enable rejection (default=False).
            - diagnostic : Enable diagnostic (default=False).
            - pulldown : Enable pulldown (default=True for voltage, False for current).
            - secondary : This ADC channel is shared with another function (default=False).

            DAC configuration:
            - use_slew : Enable slew rate control (default=False).
            - slew_rate : Slew rate if `use_slew` is True (default=0).
            - limit_current : Limit current (default=False).

        Returns: ADC value(s) if reading, or None if writing to a DAC.
        """
        if self.type == "analog" and channel is not None and channel > 7:
            raise ValueError("Invalid channel specified")

        # Read all ADC channels or analog pins.
        if channel is None:
            fmt = "<HHHHHHHH" if self.type == "analog" else "<HHHHHHHHHHHHHHHH"
            cmd = _CMD_GET_ANALOG_OA_BUS if self.type == "analog" else _CMD_GET_ANALOG_OD_BUS
            return struct.unpack(fmt, self.opta._send_cmd(self.addr, cmd))

        # Read a single ADC or RTD channel, or an analog pin.
        if channel_type is None and value is None:
            is_rtd = self.channels.get(channel, None) == "rtd"
            fmt = "<H" if self.type != "analog" else "<Bf" if is_rtd else "<BH"
            cmd = (_CMD_GET_ANALOG_OD_PIN if self.type != "analog" else
                   _CMD_GET_ANALOG_OA_PIN if not is_rtd else _CMD_GET_ANALOG_OA_RTD)
            return struct.unpack(fmt, self.opta._send_cmd(self.addr, cmd, channel))[-1]

        # Configure an ADC or a DAC channel, and/or write DAC channel
        if self.type != "analog":
            raise ValueError("Invalid command for Opta digital")

        if channel_type not in [None, "adc", "dac", "rtd"]:
            raise ValueError("Invalid channel type.")

        if channel_mode not in [None, "voltage", "current"]:
            raise ValueError("Invalid ADC channel mode.")

        if channel_type is not None:
            self.channels[channel] = channel_type

        kwargs_bool = lambda k, v : 1 if kwargs.get(k, v) else 2

        if channel_type == "rtd":
            use_3_wire = kwargs_bool("use_3_wire", False)
            current_ma = kwargs.get("current_ma", 0)
            arg = struct.pack("<BBI", channel, use_3_wire, current_ma)
            return self.opta._send_cmd(self.addr, _CMD_CFG_ANALOG_DAC, arg)

        if channel_type == "adc":
            average    = kwargs.get("average", 0)
            rejection  = kwargs_bool("rejection", False)
            diagnostic = kwargs_bool("diagnostic", False)
            pulldown   = kwargs_bool("pulldown", channel_mode == "voltage")
            secondary  = kwargs_bool("secondary", False)
            arg = struct.pack("BBBBBBB", channel, channel_mode == "current",
                              pulldown, rejection, diagnostic, average, secondary)
            return self.opta._send_cmd(self.addr, _CMD_CFG_ANALOG_ADC, arg)

        if channel_type == "dac":
            use_slew   = 1 if "slew_rate" in kwargs else 2
            slew_rate  = kwargs.get("slew_rate", 0)
            limit_curr = kwargs_bool("limit_current", channel_mode == "voltage")
            arg = struct.pack("BBBBB", channel, channel_mode == "current", limit_curr, use_slew, slew_rate)
            # No return because we may want to write DAC value, after configuring the channel.
            self.opta._send_cmd(self.addr, _CMD_CFG_ANALOG_DAC, arg)

        if value is not None:
            # Write to DAC channel
            self.opta._send_cmd(self.addr, _CMD_SET_ANALOG_DAC, struct.pack("<BHB", channel, value, 1))
            sleep_ms(150)

class Opta:
    def __init__(self, bus_id, freq=400_000, det=None):
        """
        Initializes an Opta controller.

        Parameters:
            - bus_id : The I2C bus identifier.
            - freq : I2C bus frequency (default=400_000).
            - det : GPIO pin used for bus detection (default is a PULL_UP input pin named "BUS_DETECT").
        """
        self.bus = I2C(bus_id, freq=freq)
        self.buf = memoryview(bytearray(256+2))
        self.det = Pin("BUS_DETECT", Pin.IN, Pin.PULL_UP) if det is None else det
        self.exp_types = {
            0x02 : ("digital", "Opta Digital Mechanical"),
            0x03 : ("digital", "Opta Digital Solid State"),
            0x04 : ("analog", "Opta Analog"),
            0x05 : ("digital", "UNO R4 MINIMA"),
        }
   
    def _log_debug(self, msg):
        # Blue protocol prints in blue
        logging.debug(f"\033[94m{msg}\033[0m")

    def _log_enabled(self, level):
        return logging.getLogger().isEnabledFor(level)

    def _bus_read(self, addr, buf):
        self.bus.readfrom_into(addr, buf)
        if self._log_enabled(logging.DEBUG):
            self._log_debug("Recv: " + " ".join(["%02X"%(a) for a in buf]))

    def _bus_write(self, addr, buf):
        if self._log_enabled(logging.DEBUG):
            self._log_debug("Send: " + " ".join(["%02X"%(a) for a in buf]))
        self.bus.writeto(addr, buf)

    def _crc8(self, buf, poly=0x07, crc=0x00):
        for byte in buf:
            crc ^= byte
            for bit in range(8):
                crc = (crc << 1) ^ poly if crc & 0x80 else crc << 1
        return crc & 0xFF
 
    def _send_cmd(self, addr, cmd, arg=None):
        plen = 0 if arg is None else 1 if isinstance(arg, int) else len(arg)
        fmt = "BBB" if plen == 0 else "BBBB" if plen == 1 else f"BBB{plen}s"
        struct.pack_into(fmt, self.buf, 0, cmd[0], cmd[1], plen, arg)
        self.buf[_CMD_HDR_LEN + plen] = self._crc8(self.buf[0:_CMD_HDR_LEN + plen])
        self._bus_write(addr, self.buf[0:_CMD_HDR_LEN + _CMD_CRC_LEN + plen])
        if cmd[2] == 0:
            return
        # Read response
        self._bus_read(addr, self.buf[0:_CMD_HDR_LEN + _CMD_CRC_LEN + cmd[2]])

        # Check CMD, ARG and LEN
        if (self.buf[1] != cmd[1] or self.buf[2] != cmd[2] or
            self.buf[0] != (0x03 if cmd[0] == _CMD_DIR_GET else 0x04)):
            raise ValueError("Unexpected response: " + "".join(f"{b:02X}" for b in self.buf[0:7]))

        # Check CRC
        if self.buf[_CMD_HDR_LEN + cmd[2]] != self._crc8(self.buf[0:_CMD_HDR_LEN + cmd[2]]):
            raise ValueError(f"Invalid CRC")

        return self.buf[_CMD_HDR_LEN:_CMD_HDR_LEN + cmd[2]]

    def _reset_bus(self, addr):
        self._send_cmd(addr, _CMD_CHIP_RESET, 0x56)
        sleep_ms(2000)

    def _set_address(self, addr, addr_new=None):
        if addr_new is not None:
            if self._log_enabled(logging.DEBUG):
                self._log_debug(f"set address: 0x{addr:02X} new_address: 0x{addr_new:02X}")
            return self._send_cmd(addr, _CMD_SET_ADDRESS, addr_new)
        return self._send_cmd(addr, _CMD_GET_ADDRESS)

    def enum_devices(self):
        """
        Initializes the bus, resets all expansions, and returns a list of detected expansions.
        Returns: A list of detected expansions on the bus.
        """
        detected = False
        expansion_list = []

        # Reset the first, last or temp device on the bus.
        for addr in [_MIN_ADDRESS, _MAX_ADDRESS, _TMP_ADDRESS]:
            try:
                self._reset_bus(addr)
                detected = True
                break
            except Exception as e:
                logging.debug(e)

        if not detected:
            raise RuntimeError("No expansions detected on the bus")

        addr = _MAX_ADDRESS
        # Assign temp I2C addresses to expansions.
        while not self.det.value():
            self._set_address(0x0A, addr_new=addr)
            sleep_ms(100)
            try:
                eaddr, etype = self._set_address(addr)
                if eaddr == addr:
                    addr += 1
                if self._log_enabled(logging.DEBUG):
                    self._log_debug(f"phase 1 type: 0x{etype:02X} address: 0x{eaddr:02X}")
            except Exception as e:
                logging.debug(e)

        # Assign final I2C addresses to expansions.
        for addr_new in range(_MIN_ADDRESS, _MIN_ADDRESS + addr - _MAX_ADDRESS):
            self._set_address(addr - 1, addr_new)
            sleep_ms(100)
            try:
                eaddr, etype = self._set_address(addr_new)
                addr -= 1
                if self._log_enabled(logging.DEBUG):
                    self._log_debug(f"phase 2 type: 0x{etype:02X} address: 0x{eaddr:02X}")
                expansion_list.append(Expansion(self, self.exp_types[etype][0], eaddr, self.exp_types[etype][1]))
            except Exception as e:
                logging.debug(e)

        return expansion_list
