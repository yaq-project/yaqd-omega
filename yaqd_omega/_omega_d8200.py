import asyncio
from typing import Dict, Any, List
import struct

import minimalmodbus  # type: ignore
from yaqd_core import UsesSerial, UsesUart, IsDaemon, IsSensor


parity_options = {"even": "E", "odd": "O", "none": "N"}

stop_bit_options = {"one": 1, "one_and_half": 1.5, "two": 2}


# https://assets.omega.com/manuals/M5442.pdf
#   as far as I can tell, the registers in this manual are wrong
class OmegaD8200(UsesUart, UsesSerial, IsSensor, IsDaemon):
    _kind = "omega-d8200"

    def __init__(self, name, config, config_filepath):
        print(config)
        super().__init__(name, config, config_filepath)
        self.client = minimalmodbus.Instrument(
            port=self._config["serial_port"],
            slaveaddress=self._config["modbus_address"],
            debug=False,
        )
        self.client.serial.baudrate = self._config["baud_rate"]
        self.client.serial.parity = parity_options[self._config["parity"]]
        self.client.serial.bytesize = self._config["byte_size"]
        self.client.serial.stopbits = stop_bit_options[self._config["stop_bits"]]
        self.client.serial.timeout = 0.25
        self.client.handle_local_echo = False
        self._channel_names = list()
        for index in range(7):
            self._channel_names.append(f"channel{index}")
        self._channel_units = {n: "A" for n in self._channel_names}
        asyncio.get_event_loop().create_task(self._update_measurements())

    def direct_serial_write(self, bytes):
        client.serial.write(bytes)

    async def _update_measurements(self):
        while True:
            await asyncio.sleep(0.5)
            out = dict()
            rawl = self.client.read_registers(48, 7, functioncode=3)
            # data is stored as offset binary
            # by xoring into 0x80_00, I can convert into twos complement shorts
            shortl = [i ^ 0x80_00 for i in rawl]
            intl = [struct.unpack(">h", b.to_bytes(2, "big"))[0] for b in shortl]
            for i, integer in enumerate(intl):
                out[f"channel{i}"] = integer * (0.04 / 2**16)
            out["measurement_id"] = self._measurement_id
            self._measurement_id += 1
            self._measured = out
