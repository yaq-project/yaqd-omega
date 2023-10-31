__all__ = ["OmegaPlatinum"]

import asyncio
from typing import Dict, Any, List
import struct

import minimalmodbus
from yaqd_core import UsesSerial, UsesUart, IsDaemon, HasPosition


parity_options = {"even": "E", "odd": "O", "none": "N"}

stop_bit_options = {"one": 1, "one_and_half": 1.5, "two": 2}

PV_REGISTER = 39

SV_REGISTER = 1


# https://bl831.als.lbl.gov/~gmeigs/PDF/omega_CNi16_communications.pdf
class OmegaIseriesModbus(UsesUart, UsesSerial, HasPosition, IsDaemon):
    _kind = "omega-iseries-modbus"

    def __init__(self, name, config, config_filepath):
        print(config)
        super().__init__(name, config, config_filepath)
        self.client = minimalmodbus.Instrument(port=self._config["serial_port"],
                                               slaveaddress=self._config["modbus_address"],
                                               debug=False)
        self.client.serial.baudrate = self._config["baud_rate"]
        self.client.serial.parity = parity_options[self._config["parity"]]
        self.client.serial.bytesize = self._config["byte_size"]
        self.client.serial.stopbits = stop_bit_options[self._config["stop_bits"]]
        self.client.handle_local_echo = self._config["modbus_handle_echo"]

    def direct_serial_write(self, bytes):
        client.serial.write(bytes)

    def _set_position(self, position: float) -> None:
        out = int(position * 10)
        try:
            self.client.write_register(registeraddress=SV_REGISTER,
                                    value=out,
                                    functioncode=0x06)
        except minimalmodbus.NoResponseError:
            self._set_position(position=position)

    async def update_state(self):
        while True:
            await asyncio.sleep(0.25)
            try:
                pv = self.client.read_register(PV_REGISTER) / 10.0
                sv = self.client.read_register(SV_REGISTER) / 10.0
                self._state["position"] = pv
                self._state["destination"] = sv
            except minimalmodbus.LocalEchoError:
                continue
            except minimalmodbus.InvalidResponseError:
                continue
            except minimalmodbus.NoResponseError:
                continue
            except minimalmodbus.SlaveReportedException:
                continue
