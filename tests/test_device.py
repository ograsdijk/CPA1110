import struct
from typing import Any

import pytest

from cpa1110.device import CPA1110
from cpa1110.enums import Connection, Errors, OperatingState, Warnings
from cpa1110.exceptions import CPAConnectionError, CPAProtocolError


def _encode_float(value: float) -> tuple[int, int]:
    raw = struct.pack("<f", value)
    return struct.unpack("<HH", raw)


class _FakeResponse:
    def __init__(self, registers: list[int], is_error: bool = False):
        self.registers = registers.copy()
        self._is_error = is_error

    def isError(self) -> bool:  # pymodbus-style name
        return self._is_error


class _FakeWriteResponse:
    def isError(self) -> bool:
        return False


class _FakeClient:
    def __init__(self, *args, **kwargs):
        self.connected = False
        self.read_calls = 0
        self.write_calls: list[tuple[int, int, int]] = []
        self.registers = [0] * 33

    def connect(self) -> bool:
        self.connected = True
        return True

    def close(self) -> None:
        self.connected = False

    def read_input_registers(self, address: int, count: int, device_id: int) -> Any:
        self.read_calls += 1
        return _FakeResponse(self.registers)

    def write_register(self, address: int, value: int, device_id: int):
        self.write_calls.append((address, value, device_id))
        return _FakeWriteResponse()


class _FakeClientNoneResponse(_FakeClient):
    def read_input_registers(self, address: int, count: int, device_id: int) -> Any:
        self.read_calls += 1
        return None


def test_auto_refresh_true_reads_on_get(monkeypatch):
    monkeypatch.setattr("cpa1110.device.ModbusTcpClient", _FakeClient)

    compressor = CPA1110("127.0.0.1", connection_type=Connection.TCP)
    client: Any = compressor.client
    client.registers[0] = 3

    assert compressor.operating_state == OperatingState.RUNNING
    assert client.read_calls >= 2  # initial refresh + property refresh


def test_auto_refresh_false_uses_cached_values(monkeypatch):
    monkeypatch.setattr("cpa1110.device.ModbusTcpClient", _FakeClient)

    compressor = CPA1110(
        "127.0.0.1", connection_type=Connection.TCP, auto_refresh=False
    )
    client: Any = compressor.client

    # initial refresh happened once in __init__
    initial_calls = client.read_calls
    client.registers[0] = 3

    # no automatic refresh, so cached value stays old until explicit refresh()
    assert compressor.operating_state == OperatingState.IDLING
    assert client.read_calls == initial_calls

    compressor.refresh()
    assert compressor.operating_state == OperatingState.RUNNING


def test_snapshot_and_control_calls(monkeypatch):
    monkeypatch.setattr("cpa1110.device.ModbusTcpClient", _FakeClient)

    compressor = CPA1110("127.0.0.1", connection_type=Connection.TCP, device_id=7)
    client: Any = compressor.client

    in_lo, in_hi = _encode_float(12.5)
    out_lo, out_hi = _encode_float(8.0)

    client.registers[0] = 3
    client.registers[2] = 0
    client.registers[3] = int(Warnings.COOLANT_IN_HIGH)
    client.registers[6] = in_lo
    client.registers[7] = in_hi
    client.registers[8] = out_lo
    client.registers[9] = out_hi

    snapshot = compressor.read_snapshot()
    assert snapshot.operating_state == OperatingState.RUNNING
    assert snapshot.warnings == Warnings.COOLANT_IN_HIGH
    assert snapshot.errors == Errors.COOLANT_IN_HIGH
    assert snapshot.coolant_in_temperature == 12.5
    assert snapshot.coolant_out_temperature == 8.0

    compressor.enable_compressor()
    compressor.disable_compressor()
    assert client.write_calls == [(1, 0x0001, 7), (1, 0x00FF, 7)]


def test_disconnected_access_raises_typed_connection_error(monkeypatch):
    monkeypatch.setattr("cpa1110.device.ModbusTcpClient", _FakeClient)

    compressor = CPA1110(
        "127.0.0.1",
        connection_type=Connection.TCP,
        auto_connect=False,
    )

    with pytest.raises(CPAConnectionError):
        _ = compressor.operating_state


def test_protocol_error_on_none_response(monkeypatch):
    monkeypatch.setattr("cpa1110.device.ModbusTcpClient", _FakeClientNoneResponse)

    compressor = CPA1110(
        "127.0.0.1",
        connection_type=Connection.TCP,
        auto_connect=False,
    )
    compressor.connect()

    with pytest.raises(CPAProtocolError):
        compressor.refresh()
