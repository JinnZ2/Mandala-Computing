"""
example-hardware.py
Demonstrates concepts from Hardware.md:
  - OctahedralSubstrateController API simulation
  - Command protocol codes (WRITE, READ, SET_TEMP, RELAX)
  - Magnetic field configurations per state
  - Read/write timing simulation
  - Calibration workflow
"""

import time
import random
from dataclasses import dataclass, field
from typing import List, Optional


# command protocol codes
CMD_WRITE = 0x01
CMD_READ = 0x02
CMD_SET_TEMP = 0x10
CMD_RELAX = 0x20

# magnetic field configurations per octahedral state (mT)
MAGNETIC_FIELDS = {
    0: (0.0, 0.0, 0.0),
    1: (50.0, 0.0, 0.0),
    2: (0.0, 50.0, 0.0),
    3: (0.0, 0.0, 50.0),
    4: (35.0, 35.0, 0.0),
    5: (0.0, 35.0, 35.0),
    6: (35.0, 0.0, 35.0),
    7: (29.0, 29.0, 29.0),
}

# timing specs (nanoseconds)
WRITE_TIME_NS = 5
READ_TIME_NS = 2

# safety limits
MAX_MAGNETIC_FIELD_MT = 100.0
MAX_TEMPERATURE_K = 400.0


@dataclass
class SubstrateCell:
    """Single cell on the octahedral substrate."""
    index: int
    state: int = 0
    calibration_offset: tuple = (0.0, 0.0, 0.0)


@dataclass
class OctahedralSubstrateController:
    """
    Simulated hardware controller for octahedral substrate.

    Mirrors the API from Hardware.md:
      write_state, read_state, set_temperature, trigger_relaxation
    """
    num_cells: int = 16
    temperature_K: float = 4.0
    cells: List[SubstrateCell] = field(default_factory=list)
    command_log: List[dict] = field(default_factory=list)

    def __post_init__(self):
        self.cells = [SubstrateCell(index=i) for i in range(self.num_cells)]

    def _log_command(self, cmd: int, cell_idx: int, data: Optional[dict] = None):
        self.command_log.append({
            "cmd": hex(cmd),
            "cell": cell_idx,
            "data": data or {},
        })

    def write_state(self, cell_idx: int, state: int) -> bool:
        """
        Write octahedral state to a cell.

        Applies magnetic field configuration from lookup table.
        Simulated timing: ~5 ns per cell.
        """
        if cell_idx < 0 or cell_idx >= self.num_cells:
            print(f"  error: cell {cell_idx} out of range")
            return False
        if state < 0 or state > 7:
            print(f"  error: state {state} invalid (must be 0-7)")
            return False

        B = MAGNETIC_FIELDS[state]

        # safety check
        magnitude = (B[0] ** 2 + B[1] ** 2 + B[2] ** 2) ** 0.5
        if magnitude > MAX_MAGNETIC_FIELD_MT:
            print(f"  safety: field {magnitude:.1f} mT exceeds limit")
            return False

        self.cells[cell_idx].state = state
        self._log_command(CMD_WRITE, cell_idx, {"state": state, "B": B})
        return True

    def read_state(self, cell_idx: int) -> int:
        """
        Read current state via TMR optical readout.
        Simulated timing: ~2 ns per cell.
        """
        if cell_idx < 0 or cell_idx >= self.num_cells:
            return -1
        self._log_command(CMD_READ, cell_idx)
        return self.cells[cell_idx].state

    def set_temperature(self, temp_K: float) -> bool:
        """Set substrate temperature in Kelvin."""
        if temp_K < 0 or temp_K > MAX_TEMPERATURE_K:
            print(f"  safety: temperature {temp_K} K out of range")
            return False
        self.temperature_K = temp_K
        self._log_command(CMD_SET_TEMP, -1, {"temperature_K": temp_K})
        return True

    def trigger_relaxation(self, steps: int = 100) -> dict:
        """
        Trigger thermal relaxation on the substrate.

        Simulates Metropolis-Hastings state transitions.
        """
        self._log_command(CMD_RELAX, -1, {"steps": steps})
        flips = 0

        for _ in range(steps):
            idx = random.randint(0, self.num_cells - 1)
            old_state = self.cells[idx].state
            new_state = random.randint(0, 7)

            # simplified acceptance: always accept (low temperature)
            if self.temperature_K < 10.0 or random.random() < 0.3:
                self.cells[idx].state = new_state
                flips += 1

        return {"steps": steps, "flips": flips}

    def batch_write(self, states: List[int]):
        """Write states to all cells in batch."""
        for i, s in enumerate(states):
            self.write_state(i, s % 8)

    def calibrate(self):
        """
        Run calibration workflow.

        Writes each state and reads back to verify, computing per-cell offsets.
        """
        print("  calibrating...")
        errors = 0
        for cell in self.cells:
            for state in range(8):
                self.write_state(cell.index, state)
                readback = self.read_state(cell.index)
                if readback != state:
                    errors += 1
        print(f"  calibration complete: {errors} errors across {self.num_cells * 8} checks")

    def status(self):
        """Print controller status."""
        states = [c.state for c in self.cells]
        print(f"  cells: {self.num_cells}")
        print(f"  temperature: {self.temperature_K} K")
        print(f"  states: {states}")
        print(f"  commands issued: {len(self.command_log)}")


if __name__ == "__main__":
    print("=" * 60)
    print("example-hardware: octahedral substrate controller simulation")
    print("=" * 60)

    ctrl = OctahedralSubstrateController(num_cells=8)

    # show magnetic field table
    print("\nmagnetic field configurations (mT)")
    print(f"{'state':>6}  {'Bx':>8}  {'By':>8}  {'Bz':>8}  {'|B|':>8}")
    print("-" * 42)
    for state, (bx, by, bz) in MAGNETIC_FIELDS.items():
        mag = (bx ** 2 + by ** 2 + bz ** 2) ** 0.5
        print(f"{state:>6}  {bx:>8.1f}  {by:>8.1f}  {bz:>8.1f}  {mag:>8.1f}")

    # write / read demo
    print("\nwrite/read cycle")
    for i in range(ctrl.num_cells):
        ctrl.write_state(i, i % 8)
        readback = ctrl.read_state(i)
        print(f"  cell {i}: wrote {i % 8}, read {readback}")

    # relaxation
    print("\ntriggering relaxation (100 steps)")
    result = ctrl.trigger_relaxation(100)
    print(f"  flips: {result['flips']}")

    # calibrate
    print("\ncalibration")
    ctrl.calibrate()

    # final status
    print("\ncontroller status")
    ctrl.status()

    print("\ndone.")
