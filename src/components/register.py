"""Register module"""


class Register:
    """Registers"""

    def __init__(self, size: int):
        self.registers = {i: f"r{i}" for i in range(size)}

        for reg in self.registers.values():
            setattr(self, reg, 0)

    def write(self, reg_num: int, value: int) -> None:
        """Write a value to a register"""

        if reg_num not in self.registers:
            raise ValueError("Invalid register number")
        setattr(self, self.registers[reg_num], value)

    def read(self, reg_num: int) -> int:
        """Read a value from a register"""

        if reg_num not in self.registers:
            raise ValueError("Invalid register number")
        return getattr(self, self.registers[reg_num])

    def clear(self) -> None:
        """Clear all registers"""
        for reg in self.registers.values():
            setattr(self, reg, 0)
