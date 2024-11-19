"""Program counter module"""


class ProgramCounter:
    """Program counter"""

    def __init__(self):
        self.counter = 0

    def inc(self, n=1) -> None:
        """Increment the program counter"""

        self.counter += n

    def set(self, value: int) -> None:
        """Set the program counter"""

        self.counter = value

    def get(self) -> int:
        """Get the program counter"""

        return self.counter
