"""Assembler for the ASM code"""

import os
import pathlib

from components.config import Config
from cpu import Register
from opcodes import get_opcode


def encode_instruction(
    opcode_number: int, arguments: list[tuple[str, int | None]] | None = None
) -> bytes:
    """
    Encodes an instruction with up to 2 arguments.
    Takes an opcode number (0-255) and optional arguments.
    """

    if arguments and len(arguments) > 2:
        raise ValueError("Cannot encode more than 2 arguments")

    # Start with the opcode
    encoded_instruction = [opcode_number & 0xFF]

    # Argument count (2 bits)
    arg_count = len(arguments)
    encoded_instruction[0] |= arg_count << 6

    # Argument types (2 bits each)
    arg_types = 0
    for i, (arg_type, _) in enumerate(arguments):
        if arg_type == "register":
            arg_types |= 0b00 << (i * 2)
        elif arg_type == "immediate":
            arg_types |= 0b01 << (i * 2)
        elif arg_type == "memory_address":
            arg_types |= 0b10 << (i * 2)
        elif arg_type == "register_memory":
            arg_types |= 0b11 << (i * 2)
        else:
            raise ValueError("Unsupported argument type")
    encoded_instruction.append(arg_types)

    # Argument data
    for arg_type, value in arguments:
        if arg_type in ("register", "register_memory"):
            encoded_instruction.append(value & 0b1111)  # Register ID (4 bits)
        elif arg_type == "immediate":
            encoded_instruction.extend(value.to_bytes(4, "little"))  # 32-bit immediate
        elif arg_type == "memory_address":
            encoded_instruction.extend(
                value.to_bytes(2, "little")
            )  # 16-bit memory address

    return bytes(encoded_instruction)


def get_int(value: str) -> int:
    """Get an integer value from a string"""
    try:
        value = int(value)
    except ValueError:
        value = int(value, 16)
    return value


if __name__ == "__main__":
    SCRIPT_DIR = pathlib.Path(__file__).parent

    # Getting a dummy register to get register IDs and information
    config_obj = Config()
    config_obj.load()
    dummy_register = Register(config_obj.get("register_count"))

    # First pass: Collect label positions and calculate instruction sizes
    label_positions = {}
    instruction_sizes = []  # Store sizes for each instruction
    CURRENT_POSITION = 0

    with open(
        os.path.join(SCRIPT_DIR, "code", "asm", "code.asm"), "r", encoding="utf-8"
    ) as file:
        code = file.readlines()

        # First pass - collect instruction sizes
        for line in code:
            line = line.strip().replace(",", " ").split(";")[0].strip()
            if not line:
                continue

            line_parts = line.split(" ")

            # Store current position for label if this is a label definition
            if ":" in line_parts[0]:
                label = line_parts[0][:-1]  # Remove the colon
                label_positions[label] = CURRENT_POSITION
                continue

            # Calculate instruction size
            INSTRUCTION_SIZE = 2  # Base size (opcode + arg types)
            if len(line_parts) > 1:
                args = line_parts[1:]
                for arg in args:
                    if "[" in arg:
                        if "r" in arg:
                            INSTRUCTION_SIZE += 1  # register_memory
                        else:
                            INSTRUCTION_SIZE += 2  # memory_address
                    elif "r" in arg:
                        INSTRUCTION_SIZE += 1  # register
                    else:
                        # All labels will be treated as immediates
                        INSTRUCTION_SIZE += 4  # immediate

            instruction_sizes.append(INSTRUCTION_SIZE)
            CURRENT_POSITION += INSTRUCTION_SIZE

        # Second pass - compile with resolved labels
        output = []
        for line in code:
            line = line.strip().replace(",", "").split(";")[0].strip()
            if not line:
                continue

            line_parts = line.split(" ")
            if ":" in line_parts[0]:
                continue  # Skip label declarations

            opcode = get_opcode(line_parts[0])
            args = line_parts[1:]
            parsed_args = []

            for arg in args:
                if "[" in arg:
                    if "r" in arg:
                        register_num = [
                            k
                            for k, v in dummy_register.registers.items()
                            if v == arg[1:-1]
                        ][0]
                        parsed_args.append(("register_memory", register_num))
                    else:
                        parsed_args.append(("memory_address", get_int(arg[1:-1])))
                elif "r" in arg:
                    register_num = [
                        k for k, v in dummy_register.registers.items() if v == arg
                    ][0]
                    parsed_args.append(("register", register_num))
                elif arg in label_positions:
                    # Replace label with its position
                    parsed_args.append(("immediate", label_positions[arg]))
                else:
                    parsed_args.append(("immediate", get_int(arg)))

            encoded = encode_instruction(opcode, parsed_args)
            output.append(encoded)
            print(
                f"{line.ljust(16)} - Opcode: {opcode} ({line_parts[0]}), "
                f"Args: {parsed_args}, Encoded: {encoded}"
            )

    with open(os.path.join(SCRIPT_DIR, "code", "compiled", "rom.bin"), "wb") as file:
        print(f"Total bytes: {len(b''.join(output))}")
        file.write(b"".join(output))
