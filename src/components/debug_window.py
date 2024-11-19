"""Debug window module"""

import tkinter as tk
from typing import TYPE_CHECKING

import matplotlib.backend_bases
import matplotlib.pyplot as plt

if TYPE_CHECKING:  # Avoid circular imports
    from cpu import CPU


class DebugWindow:
    """Debug window for the CPU"""

    def __init__(self, cpu_obj: "CPU", simple: bool = False):
        self.cpu = cpu_obj
        self.root = tk.Tk()
        self.root.title("CPU Debug Window" if not simple else "Simple CPU Debug Window")
        self.root.geometry("400x425" if not simple else "400x225")
        self.root.resizable(False, False)
        self.simple = simple
        self.max_graph_points = self.cpu.config.get("max_graph_points")

        # Lock for thread safety
        self._is_updating = False

        # Create main frame with padding
        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Program Counter
        self.pc_frame = tk.LabelFrame(
            self.main_frame, text="Program Counter", padx=5, pady=5
        )
        self.pc_frame.pack(fill=tk.X, pady=(0, 10))
        self.pc_label = tk.Label(self.pc_frame, text="0")
        self.pc_label.pack()

        # Current Instruction
        self.instr_frame = tk.LabelFrame(
            self.main_frame, text="Current Instruction", padx=5, pady=5
        )
        self.instr_frame.pack(fill=tk.X, pady=(0, 10))
        self.instr_label = tk.Label(self.instr_frame, text="None")
        self.instr_label.pack()

        # Instruction Time
        self.instr_time_frame = tk.LabelFrame(
            self.main_frame, text="Instruction Time", padx=5, pady=5
        )
        self.instr_time_frame.pack(fill=tk.X, pady=(0, 10))
        self.instr_time_label = tk.Label(
            self.instr_time_frame,
            text="0μs (100: 0μs)"
            if self.cpu.config.get("record_timings")
            else "DISABLED",
        )
        self.instr_time_label.pack()

        if not simple:
            # Flags
            self.flags_frame = tk.LabelFrame(
                self.main_frame, text="Flags", padx=5, pady=5
            )
            self.flags_frame.pack(fill=tk.X, pady=(0, 10))
            self.flags_label = tk.Label(self.flags_frame, text="Z: 0, N: 0, O: 0")
            self.flags_label.pack()

            # Registers
            self.reg_frame = tk.LabelFrame(
                self.main_frame, text="Registers", padx=5, pady=5
            )
            self.reg_frame.pack(fill=tk.X, pady=(0, 10))
            self.reg_labels = {}

            # Create 4x4 grid of registers
            for i in range(4):
                self.reg_frame.grid_columnconfigure(i, weight=1)
                for j in range(4):
                    reg_num = i * 4 + j
                    reg_name = self.cpu.register.registers[reg_num]
                    self.reg_labels[reg_name] = tk.Label(
                        self.reg_frame, text=f"({reg_num}) {reg_name}: 0"
                    )
                    self.reg_labels[reg_name].grid(row=j, column=i, sticky="w", padx=2)

            if self.cpu.config.get("record_timings") and self.cpu.config.get(
                "timing_graph"
            ):
                # Storage for instruction names and timing data
                self.instruction_history = []
                self.max_graph_points = self.cpu.config.get("max_graph_points")

                # Add graph update counter
                self.graph_update_counter = 0
                self.graph_update_frequency = self.cpu.config.get(
                    "graph_update_frequency"
                )

                # Matplotlib setup
                self.fig, self.ax = plt.subplots(figsize=(8, 4))
                self.fig.canvas.manager.set_window_title("CPU Instruction Times")
                (self.line,) = self.ax.plot([], [], "b-", picker=5)
                self.ax.set_xlabel("Instruction")
                self.ax.set_ylabel("Time (μs)")
                self.ax.grid(True)

                # Add annotation object (hidden by default)
                self.annot = self.ax.annotate(
                    "",
                    xy=(0, 0),
                    xytext=(10, 10),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
                    visible=False,
                )

                # Connect event handlers
                self.fig.canvas.mpl_connect("motion_notify_event", self.hover)
                plt.show(block=False)

        # Control Buttons
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 0))

        self.step_button = tk.Button(
            self.control_frame, text="Step", command=self.single_step
        )
        self.step_button.pack(side=tk.LEFT, padx=5)

        self.continue_button = tk.Button(
            self.control_frame, text="Start", command=self.toggle_continue
        )
        self.continue_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = tk.Button(
            self.control_frame, text="Reset", command=self.restart_program
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.is_continuing = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<F7>", lambda _: self.single_step())
        self.root.bind("<F6>", lambda _: self.toggle_continue())
        self.root.bind("<F5>", lambda _: self.restart_program())

        # Add mode tracking
        self.single_step_mode = True  # Start in single-step mode
        self.batch_size = self.cpu.config.get(
            "batch_size"
        )  # Only used in continuous mode
        self.update_interval = self.cpu.config.get(
            "window_update_interval"
        )  # 5 FPS for continuous mode

        self.schedule_update()
        self.root.update()

    def restart_program(self) -> None:
        """Restart the program"""

        # Stop continuous execution if running
        self.is_continuing = False
        self.continue_button.config(text="Start")

        # Reset CPU state
        self.cpu.is_halted = False
        self.cpu.program_counter.set(0)
        self.cpu.stack.clear()
        self.cpu.register.clear()
        self.cpu.ram.clear()
        self.cpu.flags = {"Z": 0, "N": 0, "O": 0, "C": 0}
        self.cpu.instruction_times.clear()
        self.cpu.instruction_count = 0
        self.cpu.current_instruction = None
        self.cpu.current_opcode = None
        self.cpu.current_operands = None

        # Reset debug window state
        self.single_step_mode = True
        self.cpu.paused = True

        # Update display if it exists
        if self.cpu.display:
            self.cpu.display.clear()
            self.cpu.display.update()

        # Reset timing graph if enabled
        if self.cpu.config.get("timing_graph") and not self.simple:
            self.instruction_history.clear()
            self.line.set_data([], [])
            self.ax.relim()
            self.ax.autoscale_view()
            try:
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
            except (ValueError, RuntimeError):
                pass  # Ignore matplotlib errors during window operations

        # Schedule a UI update
        self.root.after(1, self.update)

    def schedule_update(self) -> None:
        """Schedule debug window updates at a lower frequency"""

        if not self.cpu.is_halted:
            self.update()
            self.root.after(self.update_interval, self.schedule_update)

    def median_instruction_time(self, window_size: int) -> float:
        """Return the average instruction time in milliseconds"""

        if not self.cpu.instruction_times:
            return 0.0

        # Get the most recent measurements up to window_size
        recent_times = self.cpu.instruction_times[-window_size:]

        # Calculate average in microseconds
        return sum(recent_times) / len(recent_times)

    def format_operand(self, operand: tuple[str, int | None]) -> str:
        """Format operand with shortened type names"""

        type_, val = operand
        type_abbrev = {
            0x00: "r",
            0x01: "i",
            0x10: "m",
            0x11: "rm",
        }.get(type_, type_)
        return f"{type_abbrev}:{val}"

    def hover(self, hover_event: matplotlib.backend_bases.MouseEvent) -> None:
        """Handle mouse hover events"""
        if hover_event.inaxes != self.ax:
            self.annot.set_visible(False)
            self.fig.canvas.draw_idle()
            return

        cont, ind = self.line.contains(hover_event)
        if cont:
            # Get the x data point closest to the mouse
            x, y = self.line.get_data()
            pos = ind["ind"][0]

            # Ensure we have valid data for this position
            if pos < len(self.instruction_history) and pos < len(
                self.cpu.instruction_times
            ):
                self.annot.xy = (x[pos], y[pos])
                instr = self.instruction_history[pos]
                time_val = self.cpu.instruction_times[pos]
                self.annot.set_text(f"{instr}\n{time_val:.2f}μs")
                self.annot.set_visible(True)
            else:
                self.annot.set_visible(False)
        else:
            self.annot.set_visible(False)
        self.fig.canvas.draw_idle()

    def update(self) -> None:
        """Update the debug window"""

        # Prevent multiple simultaneous updates
        if self._is_updating:
            return

        try:
            self._is_updating = True

            # Update Program Counter
            self.pc_label.config(
                text=f"0x{self.cpu.program_counter.get():04x} "
                f"({self.cpu.program_counter.get()})"
            )

            # Update Current Instruction
            if self.cpu.current_opcode:
                operands_str = ", ".join(
                    self.format_operand(operand)
                    for operand in self.cpu.current_operands
                )
                self.instr_label.config(
                    text=f"{self.cpu.current_opcode} {operands_str}"
                )

            if self.cpu.config.get("record_timings"):
                # Update Instruction Time
                if self.cpu.instruction_times:
                    current_time = self.cpu.instruction_times[-1]
                else:
                    current_time = 0.0
                self.instr_time_label.config(
                    text=f"{current_time:.2f}μs "
                    f"(100: {self.median_instruction_time(self.max_graph_points):.2f}μs)"
                )

            if not self.simple:
                # Update Flags
                flags_str = ", ".join(
                    f"{flag}: {val}" for flag, val in self.cpu.flags.items()
                )
                self.flags_label.config(text=flags_str)

                # Update Registers
                for reg_num, reg_name in self.cpu.register.registers.items():
                    value = getattr(self.cpu.register, reg_name)
                    row = reg_num // 4
                    col = reg_num % 4
                    self.reg_labels[reg_name].grid(row=row, column=col, padx=5, pady=2)
                    self.reg_labels[reg_name].config(text=f"{reg_name}: {value}")

                # Update instruction time graph
                if (
                    self.cpu.config.get("record_timings")
                    and self.cpu.config.get("timing_graph")
                    and self.cpu.instruction_times
                ):
                    try:
                        # Store current instruction name if it exists
                        if self.cpu.current_opcode:
                            operands_str = ", ".join(
                                self.format_operand(operand)
                                for operand in self.cpu.current_operands
                            )
                            instr_name = f"{self.cpu.current_opcode} {operands_str}"
                            self.instruction_history.append(instr_name)
                            if len(self.instruction_history) > self.max_graph_points:
                                self.instruction_history = self.instruction_history[
                                    -self.max_graph_points :
                                ]

                        # Only update graph periodically
                        self.graph_update_counter += 1
                        if self.graph_update_counter >= self.graph_update_frequency:
                            self.graph_update_counter = 0

                            times = self.cpu.instruction_times[-self.max_graph_points :]

                            self.line.set_data(range(len(times)), times)
                            self.ax.relim()
                            self.ax.autoscale_view()
                            self.fig.canvas.draw()
                            self.fig.canvas.flush_events()
                    except (ValueError, RuntimeError):
                        # Ignore matplotlib errors during window operations
                        pass

        except tk.TclError:
            # Window was closed
            return
        finally:
            self._is_updating = False

    def single_step(self) -> None:
        """Perform a single CPU step"""

        if not self.cpu.is_halted:
            was_paused = self.cpu.paused
            self.cpu.paused = False
            self.cpu.step()
            if self.single_step_mode:
                self.update()  # Update immediately in single-step mode
            self.cpu.paused = was_paused
            if self.cpu.display:
                self.cpu.display.update()

    def toggle_continue(self) -> None:
        """Toggle execution state"""

        self.is_continuing = not self.is_continuing
        self.single_step_mode = not self.is_continuing  # Toggle mode
        self.cpu.paused = not self.is_continuing
        self.continue_button.config(text="Pause" if self.is_continuing else "Start")
        if self.is_continuing:
            self.continue_execution()

    def continue_execution(self) -> None:
        """Continue execution in batches"""

        if self.is_continuing and not self.cpu.is_halted:
            try:
                # Execute multiple instructions in a batch
                for _ in range(self.batch_size):
                    if not self.is_continuing or self.cpu.is_halted:
                        break
                    self.single_step()

                # Schedule next batch
                self.root.after(1, self.continue_execution)  # Schedule next batch ASAP

            except (tk.TclError, RuntimeError):
                self.on_closing()

    def on_closing(self) -> None:
        """Handle window closing"""

        self.is_continuing = False
        self.cpu.is_halted = True
        self.cpu.paused = True
        if not self.simple and self.cpu.config.get("timing_graph"):
            plt.close("all")  # Close matplotlib window
        # if pygame:
        #    pygame.quit()
        self.root.quit()
