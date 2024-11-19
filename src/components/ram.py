"""Random access memory module"""

from collections import defaultdict


class RAM:
    """Random access memory"""

    def __init__(self, size=1024):
        self.data = defaultdict(int)
        self.size = size

    def write(self, address: int, value: int) -> None:
        """Write a value to the RAM"""

        if address > self.size or address < 0:
            raise ValueError("Access violation: write")

        self.data[address] = value

    def read(self, address: int) -> int:
        """Read a value from the RAM"""

        if address > self.size or address < 0:
            raise ValueError("Access violation: read")

        return self.data[address]

    def clear(self) -> None:
        """Clear all RAM data"""

        self.data.clear()
