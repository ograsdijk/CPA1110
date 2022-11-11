from functools import wraps
from ipaddress import ip_address
from typing import Callable, Optional

from pymodbus import client
from pymodbus.constants import Defaults
from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import rtu_framer, socket_framer
from pymodbus.register_read_message import ReadInputRegistersResponse

from cpa1110.attributes import FloatProperty, to_int

from .enums import (
    Connection,
    OperatingState,
    PressureUnits,
    TemperatureUnits,
    Warnings,
    Errors,
)


def _read_input_register(func: Callable) -> Callable:
    @wraps
    def wrapper(self, *args, **kwargs):
        self._rr = self._read_input_register_reponse()
        return func(self, *args, **kwargs)

    return wrapper


class CPA1110:
    CoolantInTemperature = FloatProperty(6, 7)
    CoolantOutTemperature = FloatProperty(8, 9)
    OilTemperature = FloatProperty(10, 11)
    HeliumTemperature = FloatProperty(12, 13)
    LowPressure = FloatProperty(14, 15)
    LowPressureAverage = FloatProperty(16, 17)
    HighPressure = FloatProperty(18, 19)
    HighPressureAverage = FloatProperty(20, 21)
    DeltaPressureAverage = FloatProperty(22, 23)
    MotorCurrent = FloatProperty(24, 25)
    HoursOfOperation = FloatProperty(26, 27)

    def __init__(
        self,
        resource_name: str,
        connection_type: Connection,
        port: int = Defaults.TcpPort,
    ) -> None:
        if connection_type == Connection.SERIAL:
            self.client = client.ModbusSerialClient(
                port=resource_name,
                framer=rtu_framer.sock,
                stopbits=1,
                bytesize=8,
                parity="E",
                baudrate=9600,
            )
        elif connection_type == Connection.TCP:
            # verify IP address is in a valid format
            ip_address(resource_name)
            self.client = client.ModbusTcpClient(
                host=resource_name,
                framer=socket_framer.ModbusSocketFramer,
                port = port
            )
        else:
            raise ValueError("Cannot connect to device.")

        self._rr: ReadInputRegistersResponse = self._read_input_register_response()

    def enable_compressor(self) -> None:
        """
        Start the compressor
        """
        self.client.write_register(1, 0x0001, unit=16)

    def disable_compressor(self) -> None:
        """
        Stop the compressor
        """
        self.client.write_register(1, 0x00FF, unit=16)

    def _read_input_register_response(self) -> ReadInputRegistersResponse:
        """
        Read registers

        Returns:
            Optional[bool]: _description_
        """
        read_input_register_response = self.client.read_input_registers(
            1, count=33, slave=16
        )
        if isinstance(read_input_register_response, ModbusIOException):
            raise read_input_register_response
        else:
            return read_input_register_response

    @property
    @_read_input_register
    def OperatingState(self) -> OperatingState:
        state = to_int(self._rr.registers[0], 0)
        for operating_state in OperatingState:
            if operating_state == state:
                return operating_state
        return OperatingState.NA

    @property
    @_read_input_register
    def Warnings(self) -> Warnings:
        """
        0: No warnings
        1: Coolant IN running High
        2: Coolant IN running Low
        4: Coolant OUT running High
        8: Coolant OUT running Low
        16:  Oil running High
        32:  Oil running Low
        64:  Helium running High
        128: Helium running Low
        256:  Low Pressure running High
        512:  Low Pressure running Low
        1024: High Pressure running High
        2048: High Pressure running Low
        4096: Delta Pressure running High
        8192: Delta Pressure running Low
        131072: Static Pressure running High
        262144: Static Pressure running Low
        524288: Cold head motor Stall
        TODO: make this work
        """
        warning = to_int(self._rr.registers[3], self._rr.registers[2])
        return Warnings(warning)

    @property
    @_read_input_register
    def Errors(self) -> Errors:
        """
        0: No Errors
        1: Coolant IN High
        2: Coolant IN Low
        4: Coolant OUT High
        8: Coolant OUT Low
        16: Oil High
        32: Oil Low
        64: Helium High
        128: Helium Low
        256: Low Pressure High
        512: Low Pressure Low
        1024: High Pressure High
        2048: High Pressure Low
        4096: Delta Pressure High
        8192: Delta Pressure Low
        16384: Motor Current Low
        32768: Three Phase Error
        65536: Power Supply Error
        131072: Static Pressure High
        262144: Static Pressure Low
        """
        error = to_int(self._rr.registers[3], 0)
        return Errors(error)

    @property
    @_read_input_register
    def PressureUnits(self) -> PressureUnits:
        state = to_int(self._rr.registers[28], 0)
        for unit in PressureUnits:
            if state == unit:
                return unit
        return PressureUnits.NA

    @property
    @_read_input_register
    def TemperatureUnits(self) -> TemperatureUnits:
        state = to_int(self._rr.registers[29], 0)
        for unit in TemperatureUnits:
            if state == unit:
                return unit
        return TemperatureUnits.NA

    @property
    @_read_input_register
    def PanelSerialNumber(self):
        return to_int(self._rr.registers[30], 0)

    @property
    @_read_input_register
    def ModelNumber(self) -> int:
        """
        The upper 8 bits contain the Major model number and
        the lower 8 bits contain the Minor model number.
        Major Model Numbers consist of
            1:   800 Series
            2:   900 Series
            3:  1000 Series
            4:  1100 Series
            5:  2800 Series
        Minor Model Numbers consist of:
            1:  A1       13:  07
            2:  01       14:  H7
            3:  02       15:  I7
            4:  03       16:  08
            5:  H3       17:  09
            6:  I3       18:  9C
            7:  04       19:  10
            8:  H4       20:  1I
            9:  05       21:  11
            10: H5       22:  12
            11: I6       23:  13
            12: 06       24:  14
        Example:  A 289C compressor will give a Major of 5
        and a Minor of 18.
        """
        return to_int(self._rr.registers[31], 0)

    @property
    @_read_input_register
    def SoftwareRev(self) -> int:
        return to_int(self._rr.registers[32], 0)
