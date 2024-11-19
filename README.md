# Python-CPU
 A simple CPU emulator made with python that uses a custom simple [ISA](https://en.wikipedia.org/wiki/Instruction_set_architecture) and has its own assembler and debugger. The program comes with an example program that displays an RGB gradient onto the display.

 ## Table of Contents
- [Python-CPU](#python-cpu)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Configuration](#configuration)
  - [TODO](#todo)
  - [License](#license)

## Installation
1. Clone the repository:
```bash
 git clone https://github.com/ImShyMike/Python-CPU.git
```

2. Install dependencies:
```bash
 pip install -r requirements.txt
 ```

## Usage
- To use the CPU, run the file at `src/cpu.py`
- To make a custom program for the CPU, edit `scr/code/asm/code.asm` and then assemble it using the assembler
- To run the assembler, run the file at `scr/assembler.py`

## Configuration
The configuration file is located at `scr/config.json`. Default values:
```json
{
    "display": true, // Toggle the display
    "printing": false, // Toggle the PRT instruction (prints numbers to console)
    "record_timings": true, // Toggle the recording of instruction execution times (requires "debug")
    "debug": true, // Toggle the debugger
    "text_debug": false, // Toggle the text debugging (debug printing)
    "simple_debug": false, // Toggle the simple debugger display mode (less information, more speed) (requires "debug")
    "timing_graph": false, // Toggle the instruction time graph (requires "record_timings")
    "max_graph_points": 1000, // Set the max history points for the graph (requires "timing_graph")
    "pixel_scale": 1, // Scale for the display (requires "display")
    "display_width": 200, // Width for the display (requires "display")
    "display_height": 200, // Height for the display (requires "display")
    "bits": 32, // CPU bits
    "register_count": 16, // Register count
    "ram_size": 1024, // RAM size
    "stack_size": 1024, // Stack size
    "graph_update_frequency": 5, // How many debugger GUI updates are needed to update the graph (requires "timing_graph")
    "batch_size": 1000, // How many CPU steps to complete before updating the debugger GUI (requires "debug")
    "window_update_interval": 200 // Window update interval (in milliseconds) (requires "debug")
}
```

## TODO
- [x] CPU
- [x] Assembler
- [ ] Compiler
- [ ] Examples
- [x] Display
- [x] Debugger

## License
This project is licensed under the [MIT License](LICENSE).
