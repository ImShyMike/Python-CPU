"""Module to store all opcodes for the custom architecture"""


# Most opcodes support one of 4 argument types as the second operand:
# (unless otherwise specified or there are less than 2 arguments)

# - Immediate:                e.g. MOV r0, 10    (The value 10)
# - Register:                 e.g. MOV r0, r1    (The value in r1)
# - Memory address:           e.g. MOV r0, [10]  (The value at memory address 10)
# - Register memory address:  e.g. MOV r0, [r1]  (The address pointed to by r1)

# (r0 is just a placeholder for any register, memory address or register memory address)


# The structure of the instruction is:
# [opcode] [arg1] [arg2]

# opcode is one of the values below

# arg1 is the first operand and can be any of the above types
# (excluding immediate in most cases) and is the destination for most opcodes

# arg2 is the second operand and can also be any of the above types,
# or omitted if there are less than 2 arguments

OPCODES = {
    "NOP": 0,   # 0x00 - NOP        - No operation - does nothing
    "MOV": 1,   # 0x01 - MOV o1 o2  - Move data between registers or memory
    "ADD": 2,   # 0x02 - ADD o1 o2  - Add two values
    "SUB": 3,   # 0x03 - SUB o1 o2  - Subtract two values
    "MUL": 4,   # 0x04 - MUL o1 o2  - Multiply two values
    "DIV": 5,   # 0x05 - DIV o1 o2  - Divide two values
    "AND": 6,   # 0x06 - AND o1 o2  - Bitwise AND operation
    "OR": 7,    # 0x07 - OR o1 o2   - Bitwise OR operation
    "CMP": 8,   # 0x08 - CMP o1 o2  - Compare two values and set flags
    "JMP": 9,   # 0x09 - JMP o1     - Jump to address unconditionally
    "JZ": 10,   # 0x0A - JZ o1      - Jump if zero flag is set
    "JNZ": 11,  # 0x0B - JNZ o1     - Jump if zero flag is not set
    "CALL": 12, # 0x0C - CALL o1    - Call subroutine (push return address and jump)
    "RET": 13,  # 0x0D - RET        - Return from subroutine
    "PUSH": 14, # 0x0E - PUSH o1    - Push value onto stack
    "POP": 15,  # 0x0F - POP o1     - Pop value from stack
    "XOR": 16,  # 0x10 - XOR o1 o2  - Bitwise XOR operation
    "NAND": 17, # 0x11 - NAND o1 o2 - Bitwise NAND operation
    "NOR": 18,  # 0x12 - NOR o1 o2  - Bitwise NOR operation
    "XNOR": 19, # 0x13 - XNOR o1 o2 - Bitwise XNOR operation
    "LDR": 20,  # 0x14 - LDR o1 o2  - Load value from memory into register
    "STR": 21,  # 0x15 - STR o1 o2  - Store value from register into memory
    "JNN": 22,  # 0x16 - JNN o1     - Jump if negative flag is not set
    "JN": 23,   # 0x17 - JN o1      - Jump if negative flag is set
    "JO": 24,   # 0x18 - JO o1      - Jump if overflow flag is set
    "JNO": 25,  # 0x19 - JNO o1     - Jump if overflow flag is not set
    "NOT": 26,  # 0x1A - NOT o1     - Bitwise NOT operation
    "SHL": 27,  # 0x1B - SHL o1     - Shift left operation
    "SHR": 28,  # 0x1C - SHR o1     - Shift right operation
    "DSP": 29,  # 0x1E - DSP o1 o2  - EXTERNAL: Set pixel value
    "CLS": 30,  # 0x1F - CLS        - EXTERNAL: Clear display screen
    "BFR": 31,  # 0x20 - BFR        - EXTERNAL: Swap display buffer
    "SB": 32,   # 0x21 - SB         - EXTERNAL: Set drawing to buffer mode
    "COL": 33,  # 0x22 - COL o1     - EXTERNAL: Set drawing color
    "HLT": 34,  # 0x23 - HLT        - TERMINATE: Halt execution
    "ADI": 35,  # 0x24 - ADI o1     - Add immediate value to register
    "SBI": 36,  # 0x25 - SBI o1     - Subtract immediate value from register
    "NEG": 37,  # 0x26 - NEG o1     - Negate register value
    "JC": 38,   # 0x27 - JC o1      - Jump if carry flag is set
    "JNC": 39,  # 0x28 - JNC o1     - Jump if carry flag is not set
    "INC": 40,  # 0x29 - INC o1     - Increment register value
    "DEC": 41,  # 0x2A - DEC o1     - Decrement register value
    "CLR": 42,  # 0x2B - CLR o1     - Clear register value
    "MOD": 43,  # 0x2C - MOD o1     - Modulo register value
    "PRT": 44,  # 0x2D - PRT o1     - EXTERNAL: Print value
    "RND": 45,  # 0x2E - RND o1     - Generate random number (0-2^31)
}

OPCODE_IDS = list(OPCODES.keys())


def get_opcode(opcode: str) -> int:
    """Get opcode ID by name"""

    return OPCODES[opcode.upper()]

def get_opcode_name(opcode_id: int) -> str:
    """Get opcode name by ID"""

    return OPCODE_IDS[opcode_id]
