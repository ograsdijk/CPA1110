import struct

# utility functions (see manual pp 21-22)
def to_float(b12, b34) -> float:
    return struct.unpack("f", struct.pack("H", b12) + struct.pack("H", b34))


def to_int(b12, b34) -> int:
    return struct.unpack("i", struct.pack("H", b12) + struct.pack("H", b34))


class FloatProperty:
    def __init__(self, index1: int, index2: int, read_only: bool = True):
        self._read_only = read_only
        self._index1 = index1
        self._index2 = index2

    def __get__(self, instance, owner) -> float:
        return to_float(instance._rr(self._index1), instance._rr(self._index2))

    def __set__(self, instance, value) -> None:
        if self._read_only:
            raise ValueError(f"Read-only attribute")
