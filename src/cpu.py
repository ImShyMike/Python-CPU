"""Main CPU implementation"""

import os
import pathlib
import random
import sys
import time
from functools import lru_cache

from components.config import Config
from components.debug_window import DebugWindow
from components.display import Display, init_pygame
from components.program_counter import ProgramCounter
from components.ram import RAM
from components.register import Register
from components.rom import ROM
from components.stack import Stack
from opcodes import get_opcode_name

pygame = None  # pylint: disable=invalid-name
if __name__ == "__main__":
    # Load config (and save the default values if the config file was not found)
    config_obj = Config()
    config_obj.load()
    config_obj.save()

    # Only import pygame if not imported, config allows it and is not being ran on PyPy
    if config_obj.get("display") and sys.implementation.name != "pypy":
        import pygame

        init_pygame()


class CPU:
    """CPU"""

    def __init__(
        self,
        config: Config,
        program_counter: ProgramCounter,
        rom: ROM,
        ram: RAM,
        register: Register,
        stack: Stack,
        display: Display,
        bits: int = 32,
        debug: bool = True,
        text_debug: bool = False,
        simple_debug: bool = False,
    ):
        self.config = config

        self.is_halted = False
        self.debug = debug
        self.text_debug = text_debug
        self.simple_debug = simple_debug
        self.bits = bits
        self.max_value = 2 ** (self.bits - 1) - 1
        self.min_value = -(2 ** (self.bits - 1))

        self.program_counter = program_counter
        self.rom = rom
        self.ram = ram
        self.register = register
        self.stack = stack
        self.display = display
        self.instruction_times = []
        self.instruction_count = 0
        self.last_step_time = time.perf_counter()

        self.current_instruction = 0
        self.current_opcode = 0
        self.current_operands = []

        self.flags = {
            "Z": 0,  # Zero Flag
            "N": 0,  # Negative Flag
            "O": 0,  # Overflow Flag
            "C": 0,  # Carry Flag
        }

        self.paused = debug
        self.debug_window = None
        if self.debug:
            self.debug_window = DebugWindow(self, simple_debug)
            self.debug_window.update()

    @lru_cache(maxsize=500)
    def decode_instruction(
        self, instruction: bytes
    ) -> tuple[int, list[tuple[str, int | None]]]:
        """Decodes an encoded instruction"""

        if not instruction:
            return 0, []

        if isinstance(instruction, int):
            return 0, []

        # Read opcode
        opcode = get_opcode_name(instruction[0] & 0x3F)  # Lower 6 bits for opcode
        argument_count = (instruction[0] >> 6) & 0b11  # Upper 2 bits for argument count

        if argument_count < 1:
            return opcode, []

        # Read argument types
        argument_types = instruction[1]
        arguments = []
        offset = 2  # Arguments start at the third byte

        for n in range(argument_count):
            argument_type = (argument_types >> (n * 2)) & 0b11
            if argument_type == 0b00:  # Register
                arguments.append((argument_type, instruction[offset] & 0b1111))
                offset += 1
            elif argument_type == 0b01:  # Immediate value
                value = int.from_bytes(instruction[offset : offset + 4], "little")
                arguments.append((argument_type, value))
                offset += 4
            elif argument_type == 0b10:  # Memory address
                value = int.from_bytes(instruction[offset : offset + 2], "little")
                arguments.append((argument_type, value))
                offset += 2
            elif argument_type == 0b11:  # Register pointing to memory address
                arguments.append((argument_type, instruction[offset] & 0b1111))
                offset += 1
            else:
                raise ValueError("Unsupported argument type")

        return opcode, arguments

    def set_value(self, value: int, value_type: str, offset: int = 0) -> None:
        """Set a value"""

        if value_type == 0b00:  # Register
            self.register.write(self.current_instruction[offset], value)
        elif value_type == 0b10:  # Memory address
            self.ram.write(self.current_instruction[offset : offset + 2], value)
        else:
            raise ValueError("Unsupported argument type")

    def get_value(self, value_type: str, offset: int = 0) -> int:
        """Get a value"""

        if value_type == 0b00:  # Register
            return self.register.read(self.current_instruction[offset])
        elif value_type == 0b01:  # Immediate value
            return int.from_bytes(
                self.current_instruction[offset : offset + 4], "little"
            )
        elif value_type == 0b10:  # Memory address
            return self.ram.read(self.current_instruction[offset : offset + 2])
        else:
            raise ValueError("Unsupported argument type")

    def cap_value(self, value: int) -> int:
        """Caps a value to the CPU's bit width and handles overflow and carry"""

        # Check for carry
        if value >= 2**self.bits:
            self.set_flag("C", 1)
        elif value < 0:
            self.set_flag("C", 1)  # Set carry on negative (borrow)
        else:
            self.set_flag("C", 0)

        # Handle overflow by wrapping around using modulo
        if value > self.max_value or value < self.min_value:
            value = value % (2**self.bits)
            self.set_flag("O", 1)

            # Convert to signed value if needed
            if value > self.max_value:
                value -= 2**self.bits
        else:
            self.set_flag("O", 0)

        return value

    def get_operand_value(self, operand: tuple[str, int | None]) -> int:
        """Helper function to get actual value from any operand type"""

        op_type, op_value = operand
        if op_type == 0b00:  # Register
            return self.register.read(op_value)
        elif op_type == 0b01:  # Immediate value
            return op_value
        elif op_type == 0b10:  # Memory address
            return self.ram.read(op_value)
        elif op_type == 0b11:  # Register pointing to memory address
            addr = self.register.read(op_value)
            return self.ram.read(addr)
        else:
            raise ValueError(f"Invalid operand type: {op_type}")

    def write_result(self, operand: tuple[str, int | None], value: int) -> None:
        """Helper function to write a value with any data type"""

        op_type, op_value = operand
        if op_type == 0b00:  # Register
            self.register.write(op_value, value)
        elif op_type == 0b10:  # Memory address
            self.ram.write(op_value, value)
        elif op_type == 0b11:  # Register pointing to memory address
            addr = self.register.read(op_value)
            self.ram.write(addr, value)
        else:
            raise ValueError(f"Cannot write to operand type: {op_type}")

    def execute_instruction(
        self, opcode: int, operands: list[tuple[str, int | None]]
    ) -> None:
        """Execute an instruction"""

        if self.text_debug:
            print(f"Executing: {opcode} {operands}")
            print(f"PC: {self.program_counter.get()}")
            print(f"Flags: {self.flags}")

        if opcode == "NOP":
            pass
        elif opcode == "MOV":
            value = self.cap_value(self.get_operand_value(operands[1]))
            self.write_result(operands[0], value)
        elif opcode == "ADD":
            value = self.cap_value(
                self.get_operand_value(operands[0])
                + self.get_operand_value(operands[1])
            )
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "SUB":
            value = self.cap_value(
                self.get_operand_value(operands[0])
                - self.get_operand_value(operands[1])
            )
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "INC":
            value = self.cap_value(self.get_operand_value(operands[0]) + 1)
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "DEC":
            value = self.cap_value(self.get_operand_value(operands[0]) - 1)
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "MUL":
            value = self.cap_value(
                self.get_operand_value(operands[0])
                * self.get_operand_value(operands[1])
            )
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "DIV":
            value = self.cap_value(
                self.get_operand_value(operands[0])
                // self.get_operand_value(operands[1])
            )
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "MOD":
            value = self.cap_value(
                self.get_operand_value(operands[0])
                % self.get_operand_value(operands[1])
            )
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "AND":
            value = self.get_operand_value(operands[0]) & self.get_operand_value(
                operands[1]
            )
            self.write_result(operands[0], value)
            self.set_flags_boolean(value)
        elif opcode == "OR":
            value = self.get_operand_value(operands[0]) | self.get_operand_value(
                operands[1]
            )
            self.write_result(operands[0], value)
            self.set_flags_boolean(value)
        elif opcode == "XOR":
            value = self.get_operand_value(operands[0]) ^ self.get_operand_value(
                operands[1]
            )
            self.write_result(operands[0], value)
            self.set_flags_boolean(value)
        elif opcode == "NOT":
            value = ~self.get_operand_value(operands[0])
            self.write_result(operands[0], value)
            self.set_flags_boolean(value)
        elif opcode == "NEG":
            value = -self.get_operand_value(operands[0])
            self.write_result(operands[0], value)
            self.set_flags_arithmetic(value)
        elif opcode == "CLR":
            self.write_result(operands[0], 0)
            self.write_result(operands[1], 0)
        elif opcode == "TEST":
            result = self.get_operand_value(operands[0]) & self.get_operand_value(
                operands[1]
            )
            self.set_flags_boolean(result)
        elif opcode == "SHL":
            self.register.write(
                operands[0][1],
                self.get_operand_value(operands[0])
                << self.get_operand_value(operands[1]),
            )
            self.set_flags_arithmetic(operands[0][1])
        elif opcode == "SHR":
            self.register.write(
                operands[0][1],
                self.get_operand_value(operands[0])
                >> self.get_operand_value(operands[1]),
            )
            self.set_flags_arithmetic(operands[0][1])
        elif opcode == "CMP":
            result = self.cap_value(
                self.get_operand_value(operands[0])
                - self.get_operand_value(operands[1])
            )
            self.set_flags_arithmetic(result)
        elif opcode == "JMP":
            self.program_counter.set(self.get_operand_value(operands[0]))
            return
        elif opcode == "CALL":
            self.stack.push(self.program_counter.get())
            self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "RET":
            self.program_counter.set(self.stack.pop())
        elif opcode == "PUSH":
            self.stack.push(self.get_operand_value(operands[0]))
        elif opcode == "POP":
            self.register.write(operands[0][1], self.stack.pop())
        elif opcode == "LDR":
            self.register.write(operands[0][1], self.get_operand_value(operands[1]))
        elif opcode == "STR":
            self.ram.write(operands[0][1], self.get_operand_value(operands[1]))
        elif opcode == "JZ":
            if self.flags["Z"] == 1:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "JNZ":
            if self.flags["Z"] == 0:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "JO":
            if self.flags["O"] == 1:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "JNO":
            if self.flags["O"] == 0:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "JNN":
            if self.flags["N"] == 0:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "JN":
            if self.flags["N"] == 1:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "JC":
            if self.flags["C"] == 1:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "JNC":
            if self.flags["C"] == 0:
                self.program_counter.set(self.get_operand_value(operands[0]))
        elif opcode == "DSP":
            if self.display:
                self.display.set_pixel(
                    self.get_operand_value(operands[0]),
                    self.get_operand_value(operands[1]),
                )
        elif opcode == "CLS":
            if self.display:
                self.display.clear_image()
        elif opcode == "BFR":
            if self.display:
                self.display.swap_buffer()
        elif opcode == "SB":
            if self.display:
                self.display.set_drawing_to_buffer(self.get_operand_value(operands[0]))
        elif opcode == "COL":
            if self.display:
                self.display.set_color(self.get_operand_value(operands[0]))
        elif opcode == "RND":
            self.write_result(operands[0], random.randint(0, 2**31 - 1))
        elif opcode == "PRT":
            if self.config.get("printing"):
                print(self.get_operand_value(operands[0]))
        elif opcode == "HLT":
            self.is_halted = True
        else:
            raise ValueError(f"Invalid opcode: {opcode}")

    def set_flags_arithmetic(self, value: int) -> None:
        """Set flags based on arithmetic result"""

        # Check for negative
        if value < 0:
            self.set_flag("N", 1)
        else:
            self.set_flag("N", 0)

        # Check for zero
        if value == 0:
            self.set_flag("Z", 1)
        else:
            self.set_flag("Z", 0)

    def set_flags_boolean(self, value: int) -> None:
        """Set flags based on boolean result"""

        if value == 0:
            self.set_flag("Z", 1)
        else:
            self.set_flag("Z", 0)

        # Clear negative, carry and overflow flag
        self.set_flag("N", 0)
        self.set_flag("C", 0)
        self.set_flag("O", 0)

    def set_flag(self, flag: str, value: int) -> None:
        """Set a flag"""

        self.flags[flag] = value

    def fetch_instruction(self) -> bytes | None:
        """Fetch an instruction from the ROM"""

        if self.program_counter.get() >= self.rom.size:
            self.is_halted = True
            return None

        # Read first byte (opcode + arg count)
        first_byte = self.rom.read(self.program_counter.get())
        arg_count = (first_byte >> 6) & 0x03  # Upper 2 bits

        # Read second byte (argument types)
        arg_types_byte = self.rom.read(self.program_counter.get() + 1)

        # Calculate instruction size
        instruction_size = 2  # Base size (opcode + arg types)
        for i in range(arg_count):
            arg_type = (arg_types_byte >> (i * 2)) & 0x03
            if (
                arg_type == 0b00 or arg_type == 0b11
            ):  # Register or register pointing to memory address
                instruction_size += 1
            elif arg_type == 0b01:  # Immediate
                instruction_size += 4
            elif arg_type == 0b10:  # Memory address
                instruction_size += 2

        # Read the complete instruction
        instruction = self.rom.read_bytes(self.program_counter.get(), instruction_size)

        if self.text_debug:
            print(
                f"Fetched instruction at PC={self.program_counter.get()}: {instruction.hex()}"
            )

        # Increment the program counter
        self.program_counter.inc(instruction_size)

        return instruction

    def step(self) -> None:
        """Step through the CPU"""
        if self.is_halted or self.paused:
            return

        if self.config.get("record_timings"):
            # Calculate time since last step
            current_time = time.perf_counter()
            step_duration = (
                current_time - self.last_step_time
            ) * 1_000_000  # Convert to microseconds
            self.last_step_time = current_time

            # Add the step time to our measurements (if this isn't the first step)
            if self.instruction_count > 0:
                self.instruction_times.append(step_duration)
                # Keep a rolling window of the last 100 measurements
                if len(self.instruction_times) > 1000:
                    self.instruction_times.pop(0)

        # Fetch
        self.current_instruction = self.fetch_instruction()
        if self.current_instruction is None:
            self.is_halted = True
            return

        # Decode
        self.current_opcode, self.current_operands = self.decode_instruction(
            self.current_instruction
        )

        # Execute
        if self.current_opcode:
            self.execute_instruction(self.current_opcode, self.current_operands)

        # Update display if needed
        if self.display and self.display.needs_update:
            self.display.update()

        self.instruction_count += 1

    def pause(self) -> None:
        """Pause the CPU"""

        self.paused = True

    def resume(self) -> None:
        """Resume the CPU"""

        self.paused = False

    def run(self) -> None:
        """Run the CPU"""

        try:
            # Start the Tkinter main loop if in debug mode
            if self.debug:
                self.debug_window.root.mainloop()
            else:
                while not self.is_halted:
                    self.step()
                    if self.display:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.is_halted = True
                                break
                        self.display.update()

        except KeyboardInterrupt:
            self.is_halted = True
        finally:
            if self.config.get("text_debug"):
                print(f"Exiting. Executed {self.instruction_count} instructions.")
            if self.debug_window:
                self.debug_window.on_closing()
            else:
                if pygame:
                    pygame.quit()


if __name__ == "__main__":
    SCRIPT_DIR = pathlib.Path(__file__).parent
    rom_path = os.path.join(SCRIPT_DIR, "code", "compiled", "rom.bin")

    # Check if ROM file exists
    if not os.path.exists(rom_path):
        print("Error: ROM file not found. Please compile an assembly file first.")
        print(f"Expected path: {rom_path}")
        sys.exit(1)

    try:
        with open(rom_path, "rb") as file:
            rom_data = file.read()

        if not rom_data:
            print("Error: ROM file is empty. Please compile an assembly file first.")
            sys.exit(1)

    except (FileNotFoundError, IOError, PermissionError) as e:
        print(f"Error reading ROM file: {e}")
        sys.exit(1)

    display_obj = (
        Display(
            config_obj.get("display_width"),
            config_obj.get("display_height"),
            config_obj.get("pixel_scale"),
        )
        if pygame and config_obj.get("display")
        else None
    )

    cpu = CPU(
        config_obj,
        ProgramCounter(),
        ROM(rom_data),
        RAM(config_obj.get("ram_size")),
        Register(config_obj.get("register_count")),
        Stack(config_obj.get("stack_size")),
        display_obj,
        bits=config_obj.get("bits"),
        debug=config_obj.get("debug"),
        text_debug=config_obj.get("text_debug"),
        simple_debug=config_obj.get("simple_debug"),
    )

    cpu.run()  # Run the CPU
