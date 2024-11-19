"""Read-only memory module"""


class ROM:
    """Read-only memory"""

    def __init__(self, data=bytes):
        self.size = len(data)
        self.data = bytearray(data)

    def read(self, address: int) -> int:
        """Read a byte from the ROM"""

        return self.data[address]

    def read_bytes(self, start: int, length: int) -> bytes:
        """Read a number of bytes from the ROM"""

        return bytes(self.data[start : start + length])
