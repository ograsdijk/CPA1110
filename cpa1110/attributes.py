"""Register decoding helpers and descriptor types for CPA1110."""

import struct
from typing import Any


def to_float(b12, b34) -> float:
    """Decode two 16-bit registers into a little-endian IEEE754 float."""
    raw = struct.pack("<HH", b12 & 0xFFFF, b34 & 0xFFFF)
    return struct.unpack("<f", raw)[0]


def to_int(b12, b34) -> int:
    """Decode two 16-bit registers into a little-endian signed 32-bit int."""
    raw = struct.pack("<HH", b12 & 0xFFFF, b34 & 0xFFFF)
    return struct.unpack("<i", raw)[0]


class FloatProperty:
    """Descriptor mapping a 32-bit float register pair to a read-only property."""

    def __init__(self, index1: int, index2: int, read_only: bool = True):
        self._read_only = read_only
        self._index1 = index1
        self._index2 = index2

    def __get__(self, instance: Any, owner: Any) -> "float | FloatProperty":
        if instance is None:
            return self
        instance._maybe_refresh()
        return to_float(
            instance._rr.registers[self._index1], instance._rr.registers[self._index2]
        )

    def __set__(self, instance, value) -> None:
        """Prevent assignment to device-backed read-only properties."""
        if self._read_only:
            raise ValueError("Read-only attribute")
