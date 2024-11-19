"""Stack module"""


class Stack:
    """Stack"""

    def __init__(self, size=1024):
        self.data = []
        self.size = size

    def push(self, x: int) -> None:
        """Push a value onto the stack"""

        if len(self.data) >= self.size:
            raise ValueError("Stack overflow")
        self.data.append(x)

    def pop(self) -> int:
        """Pop a value off the stack"""

        if len(self.data) < 1:
            raise ValueError("Empty stack")

        return self.data.pop(-1)

    def clear(self) -> None:
        """Clear all stack data"""

        self.data.clear()
