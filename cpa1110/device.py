"""Synchronous client for reading and controlling a Cryomech CPA1110."""

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any

from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import FramerType

from cpa1110.attributes import FloatProperty, to_float, to_int
from cpa1110.exceptions import CPAConnectionError, CPAProtocolError

from .enums import (
    Connection,
    Errors,
    OperatingState,
    PressureUnits,
    TemperatureUnits,
    Warnings,
)


@dataclass(frozen=True, slots=True)
class CPASnapshot:
    """Decoded values from a single Modbus input-register read."""

    operating_state: OperatingState
    warnings: Warnings
    errors: Errors
    coolant_in_temperature: float
    coolant_out_temperature: float
    oil_temperature: float
    helium_temperature: float
    low_pressure: float
    low_pressure_average: float
    high_pressure: float
    high_pressure_average: float
    delta_pressure_average: float
    motor_current: float
    hours_of_operation: float
    pressure_units: PressureUnits
    temperature_units: TemperatureUnits
    panel_serial_number: int
    model_number: int
    software_rev: int


class CPA1110:
    """High-level interface for CPA1110 telemetry and control registers."""

    # Float telemetry values are represented as two 16-bit input registers.
    coolant_in_temperature = FloatProperty(6, 7)
    coolant_out_temperature = FloatProperty(8, 9)
    oil_temperature = FloatProperty(10, 11)
    helium_temperature = FloatProperty(12, 13)
    low_pressure = FloatProperty(14, 15)
    low_pressure_average = FloatProperty(16, 17)
    high_pressure = FloatProperty(18, 19)
    high_pressure_average = FloatProperty(20, 21)
    delta_pressure_average = FloatProperty(22, 23)
    motor_current = FloatProperty(24, 25)
    hours_of_operation = FloatProperty(26, 27)

    def __init__(
        self,
        resource_name: str,
        connection_type: Connection,
        port: int = 502,
        device_id: int = 16,
        auto_refresh: bool = True,
        auto_connect: bool = True,
    ) -> None:
        """Initialize a CPA1110 client.

        Args:
            resource_name: TCP host/IP or serial port path.
            connection_type: Transport type (`Connection.TCP` or `Connection.SERIAL`).
            port: TCP port when using TCP transport.
            device_id: Modbus device/slave identifier.
            auto_refresh: Refresh cached registers automatically on property access.
            auto_connect: Connect and perform an initial refresh during initialization.
        """
        self.device_id = device_id
        self.auto_refresh = auto_refresh
        self._connected = False

        if connection_type == Connection.SERIAL:
            self.client = ModbusSerialClient(
                port=resource_name,
                framer=FramerType.RTU,
                stopbits=1,
                bytesize=8,
                parity="E",
                baudrate=9600,
            )
        elif connection_type == Connection.TCP:
            # verify IP address is in a valid format
            ip_address(resource_name)
            self.client = ModbusTcpClient(host=resource_name, port=port)
        else:
            raise CPAConnectionError("Unsupported connection type")

        if auto_connect:
            self.connect()

        self._rr: Any = None
        if auto_connect:
            self.refresh()

    def __enter__(self) -> "CPA1110":
        """Support context-manager usage."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close the client on context-manager exit."""
        self.close()

    def connect(self) -> None:
        """Open the Modbus connection."""
        if self._connected:
            return
        connected = self.client.connect()
        if connected is False:
            raise CPAConnectionError("Failed to connect to CPA1110")
        self._connected = True

    def close(self) -> None:
        """Close the Modbus connection."""
        self.client.close()
        self._connected = False

    def _ensure_connected(self) -> None:
        """Raise if the client is not connected."""
        if not self._connected:
            raise CPAConnectionError("Device is not connected. Call connect() first.")

    def refresh(self) -> None:
        """Refresh cached register values from the device."""
        self._ensure_connected()
        self._rr = self._read_input_register_response()

    def _maybe_refresh(self) -> None:
        """Refresh only when automatic refresh is enabled."""
        if self.auto_refresh:
            self.refresh()

    def enable_compressor(self) -> None:
        """
        Start the compressor
        """
        self._ensure_connected()
        response = self.client.write_register(1, 0x0001, device_id=self.device_id)
        if hasattr(response, "isError") and response.isError():
            raise CPAProtocolError(f"Modbus exception response: {response}")

    def disable_compressor(self) -> None:
        """
        Stop the compressor
        """
        self._ensure_connected()
        response = self.client.write_register(1, 0x00FF, device_id=self.device_id)
        if hasattr(response, "isError") and response.isError():
            raise CPAProtocolError(f"Modbus exception response: {response}")

    def _read_input_register_response(self) -> Any:
        """Read and validate the raw input-register response."""
        read_input_register_response = self.client.read_input_registers(
            1, count=33, device_id=self.device_id
        )
        if isinstance(read_input_register_response, ModbusIOException):
            raise CPAProtocolError("I/O error while reading input registers") from read_input_register_response
        if read_input_register_response is None:
            raise CPAProtocolError("No response received from CPA1110")
        if (
            hasattr(read_input_register_response, "isError")
            and read_input_register_response.isError()
        ):
            raise CPAProtocolError(
                f"Modbus exception response: {read_input_register_response}"
            )

        registers = getattr(read_input_register_response, "registers", None)
        if registers is None or len(registers) < 33:
            raise CPAProtocolError("Unexpected register payload from CPA1110")
        return read_input_register_response

    @staticmethod
    def _coerce_operating_state(value: int) -> OperatingState:
        """Map integer value to `OperatingState` with `NA` fallback."""
        for operating_state in OperatingState:
            if operating_state == value:
                return operating_state
        return OperatingState.NA

    @staticmethod
    def _coerce_pressure_units(value: int) -> PressureUnits:
        """Map integer value to `PressureUnits` with `NA` fallback."""
        for unit in PressureUnits:
            if value == unit:
                return unit
        return PressureUnits.NA

    @staticmethod
    def _coerce_temperature_units(value: int) -> TemperatureUnits:
        """Map integer value to `TemperatureUnits` with `NA` fallback."""
        for unit in TemperatureUnits:
            if value == unit:
                return unit
        return TemperatureUnits.NA

    def read_snapshot(self) -> CPASnapshot:
        """Read one register snapshot and return decoded values."""
        self.refresh()
        registers = self._rr.registers
        return CPASnapshot(
            operating_state=self._coerce_operating_state(to_int(registers[0], 0)),
            warnings=Warnings(to_int(registers[3], registers[2])),
            errors=Errors(to_int(registers[3], 0)),
            coolant_in_temperature=to_float(registers[6], registers[7]),
            coolant_out_temperature=to_float(registers[8], registers[9]),
            oil_temperature=to_float(registers[10], registers[11]),
            helium_temperature=to_float(registers[12], registers[13]),
            low_pressure=to_float(registers[14], registers[15]),
            low_pressure_average=to_float(registers[16], registers[17]),
            high_pressure=to_float(registers[18], registers[19]),
            high_pressure_average=to_float(registers[20], registers[21]),
            delta_pressure_average=to_float(registers[22], registers[23]),
            motor_current=to_float(registers[24], registers[25]),
            hours_of_operation=to_float(registers[26], registers[27]),
            pressure_units=self._coerce_pressure_units(to_int(registers[28], 0)),
            temperature_units=self._coerce_temperature_units(to_int(registers[29], 0)),
            panel_serial_number=to_int(registers[30], 0),
            model_number=to_int(registers[31], 0),
            software_rev=to_int(registers[32], 0),
        )

    @property
    def operating_state(self) -> OperatingState:
        """Current compressor operating state."""
        self._maybe_refresh()
        state = to_int(self._rr.registers[0], 0)
        return self._coerce_operating_state(state)

    @property
    def warnings(self) -> Warnings:
        """Current warning bitfield as a `Warnings` flag set."""
        self._maybe_refresh()
        warning_value = to_int(self._rr.registers[3], self._rr.registers[2])
        return Warnings(warning_value)

    @property
    def errors(self) -> Errors:
        """Current error bitfield as an `Errors` flag set."""
        self._maybe_refresh()
        error_value = to_int(self._rr.registers[3], 0)
        return Errors(error_value)

    @property
    def pressure_units(self) -> PressureUnits:
        """Pressure unit configuration reported by the controller."""
        self._maybe_refresh()
        state = to_int(self._rr.registers[28], 0)
        return self._coerce_pressure_units(state)

    @property
    def temperature_units(self) -> TemperatureUnits:
        """Temperature unit configuration reported by the controller."""
        self._maybe_refresh()
        state = to_int(self._rr.registers[29], 0)
        return self._coerce_temperature_units(state)

    @property
    def panel_serial_number(self) -> int:
        """Digital panel serial number."""
        self._maybe_refresh()
        return to_int(self._rr.registers[30], 0)

    @property
    def model_number(self) -> int:
        """Model identifier (major/minor packed into one integer value)."""
        self._maybe_refresh()
        return to_int(self._rr.registers[31], 0)

    @property
    def software_rev(self) -> int:
        """Controller software revision value."""
        self._maybe_refresh()
        return to_int(self._rr.registers[32], 0)
