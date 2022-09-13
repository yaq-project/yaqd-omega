__all__ = ["OmegaPlatinum"]

import asyncio
from typing import Dict, Any, List
import struct

from pymodbus.client.sync import ModbusSerialClient  # type: ignore
from yaqd_core import IsSensor, UsesSerial, UsesUart, HasMeasureTrigger, IsDaemon


CURRENT_VALUE_ADDRESS = 528
PEAK_VALUE_ADDRESS = 550
VALLEY_VALUE_ADDRESS = 552
UNITS_ADDRESS = 585
UNITS = {0: None, 1: "degC", 2: "degF"}


# https://assets.omega.com/manuals/M5458.pdf
class OmegaPlatinum(UsesUart, UsesSerial, HasMeasureTrigger, IsSensor, IsDaemon):
    _kind = "omega-platinum"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self.client = ModbusSerialClient(port="/dev/ttyACM0", method="RTU")
        self.client.baudrate = 19_200
        self.client.parity = "O"
        self.client.bytesize = 8
        self.client.stopbits = 1
        self._channel_names = ["current", "peak", "valley"]
        # read unit
        if self._config["units"] is not None:
            unit = self._config["units"]
        else:
            response = self.client.read_holding_registers(address=UNITS_ADDRESS, count=1)
            unit = UNITS[response.registers[0]]
        self._channel_units = {k: unit for k in self._channel_names}

    def direct_serial_write(self, bytes):
        client.serial.write(bytes)

    async def _measure(self):
        out = {}
        # current input value
        response = self.client.read_holding_registers(address=528, count=2)
        b = ((response.registers[0] << 16) + response.registers[1]).to_bytes(4, "big")
        out["current"] = struct.unpack(">f", b)[0]
        await asyncio.sleep(0)
        # peak value
        response = self.client.read_holding_registers(address=528, count=2)
        b = ((response.registers[0] << 16) + response.registers[1]).to_bytes(4, "big")
        out["peak"] = struct.unpack(">f", b)[0]
        # valley value
        response = self.client.read_holding_registers(address=528, count=2)
        b = ((response.registers[0] << 16) + response.registers[1]).to_bytes(4, "big")
        out["valley"] = struct.unpack(">f", b)[0]
        if self._looping:
            await asyncio.sleep(0.1)
        print(out)
        return out
