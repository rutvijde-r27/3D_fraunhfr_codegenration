# Introduction

## 3D Fraunhofer G-Code Generator
### Automated Electrochemical Plate Scanning on a Modified FDM 3D Printer

*Fraunhofer Institute · Electrochemistry Automation Project · June 2026*

---

## The Problem This Solves

Electrochemical experiments often require systematically scanning a probe across the surface of a liquid-filled plate — moving in a defined grid, measuring at each point, and returning reliable, reproducible data.

Doing this by hand is slow, inconsistent, and error-prone. Even small deviations in the probe path or depth invalidate results. Doing it with expensive commercial motion platforms is accurate but rigid — you cannot easily reprogram the scan pattern for different plate geometries or experimental setups.

This project takes a different approach: it repurposes a consumer-grade FDM 3D printer — the **Anycubic Mega X** — as a precision XYZ motion platform. The extruder is not used. The machine simply moves. And because it is driven by standard G-code, a Python program can describe any scan geometry and output a file the printer executes exactly.

The result is a fully automated, fully configurable, low-cost scanning system — built from off-the-shelf hardware and open-source software.

---

## What the Software Does

The G-Code Generator takes experimental parameters as input and writes a `.gcode` file:

- **Plate dimensions** — how large is the electrochemical plate?
- **Scan pattern** — which path should the probe follow?
- **Sub-region** — scan the whole plate, or just the centre?
- **Z-depth** — how far should the probe descend to contact the liquid surface?
- **Speed** — how fast should the probe move during scanning?

From these inputs, the software calculates exact XYZ coordinates for every movement, inserts safety checks, adds the required pre-scan skirting and chemical settling pause, and writes the complete G-code file ready to load onto the printer.

No manual coordinate calculation. No risk of unsafe values. One file, ready to run.

---

## How the Printer Is Set Up

The Anycubic Mega X is used in its standard mechanical configuration. The key modification is in the **coordinate system**: a one-time calibration file (`homeZ12.gcode`) moves the print head to the physical centre of the mounted plate and resets the origin to (0, 0, 0). From that point on, all scan coordinates are expressed relative to the plate centre — intuitive for laboratory use and independent of the printer's native bed geometry.

The Z-axis is calibrated so that **Z = 0 is the probe at calibrated home height**. Negative Z moves the probe downward toward the plate surface. A hard software limit of −13.0 mm prevents the probe from ever contacting the plate holder or causing mechanical damage.

---

## Two Modules

As the project evolved, two distinct scanning modules were developed:

### Serpentine Code & GUI

The original module. It generates three scan patterns:

**Serpentine X** sweeps the probe horizontally across the plate in alternating left-to-right and right-to-left passes, stepping downward in Y after each line. This produces uniform horizontal coverage and is the most commonly used pattern for rectangular plates.

**Serpentine Y** is the vertical equivalent — alternating upward and downward passes stepping rightward in X. Useful when the plate geometry or electrode orientation favours vertical scanning.

**Diagonal** sweeps at a user-defined angle between 0° and 179°. This is particularly useful for anisotropic surfaces, for reducing systematic spatial bias, or for aligning the scan direction with a specific feature of the electrochemical cell.

All three patterns support sub-region scanning: you can define a smaller area to scan within the plate, and the tool automatically centres it with equal margins on all sides.

### Circling and Serpentine

The extended module, developed to support experiments requiring a different probe conditioning sequence before the main scan. It adds **circular scan paths** — the probe traces one or more concentric circular loops around the plate centre before the serpentine scan begins.

This is valuable when the electrochemical interface needs to be conditioned radially before linear scanning, or when the experiment involves circular electrode geometries. The circling phase and the serpentine phase are both configurable and can be combined in different sequences.

---

## Every Scan Follows the Same Structure

Regardless of module or pattern, every generated G-code file follows an identical four-phase sequence:

**Phase 1 — Skirting.** The probe traces two concentric rectangular perimeters around the scan area. This primes the probe, clears any surface debris, and allows the electrochemical interface to begin stabilising.

**Phase 2 — Pause.** A mandatory 90-second dwell is inserted. The printer waits motionless while the chemical system equilibrates. This pause is enforced in software and cannot be skipped.

**Phase 3 — Scan.** The chosen pattern executes. Every scan line is a `G1` move (recorded, feedrate-controlled). Travel between lines uses `G0` (rapid, unrecorded) at a safe Z clearance of +2 mm above the plate.

**Phase 4 — Return.** The probe rises to the travel height and returns to the plate centre (0, 0). Stepper motors are disabled.

---

## Two Interfaces

Each module provides two ways to run it:

**GUI Wizard** (`gcode_gui.py`) — A graphical window built with CustomTkinter. Fields are clearly labelled, patterns are selectable from a dropdown, and validation errors appear as dialog popups. Recommended for new users and for anyone working in a lab environment where typing commands is inconvenient.

**CLI Generator** (`gcode_generator.py`) — A terminal prompt sequence. Faster to operate once the parameters are familiar. Identical output to the GUI. Useful for scripting or remote sessions.

Both interfaces run the same validation and generation logic. The output files are identical regardless of which interface was used.

---

## Safety

Two hard limits are enforced in software and cannot be overridden by user input:

The **Z-depth limit** of −13.0 mm ensures the probe never contacts the plate holder or mechanical structure below the plate. Any input below this value is rejected before G-code is written.

The **speed limit** of 6000 mm/min (100 mm/s) ensures the stepper motors operate within reliable bounds. Above this speed, steps can be lost, positional accuracy degrades, and scan data becomes unreliable.

Input validation also checks geometric consistency: that the sub-region fits within the plate, that the number of lines fits within the scan span at the given gap, and that all dimensions are physically meaningful.

---

## Project History

The project began with a basic serpentine scan generator — a single Python script producing simple back-and-forth patterns for one plate size. Over time, it was extended with:

- A graphical interface to make it accessible to non-programmers
- Sub-region scanning for partial plate coverage
- Diagonal patterns for anisotropic experiments
- The Circling and Serpentine module for radial conditioning
- A full validation layer to prevent unsafe G-code from ever being written

The `Initial run codes/` folder preserves the early prototype scripts — useful as reference for understanding the evolution of the codebase, but not for production use.

---

## Environment

| Requirement | Detail |
|---|---|
| Python | 3.10 or higher |
| CustomTkinter | GUI framework — `pip install customtkinter` |
| Operating system | Windows, macOS, or Linux |
| Printer | Anycubic Mega X (modified for electrochemistry) |
| Internet | Not required — fully offline |

---

## Documentation Map

| Document | Location | Contents |
|---|---|---|
| Quick start & setup | `README.md` | Installation, folder structure, quick reference |
| This document | `Introduction.md` | Project background, module overview, design rationale |
| Serpentine manual | `manuals/MANUAL_Serpentine.md` | Full technical reference for serpentine patterns |
| Circling + Serpentine manual | `manuals/MANUAL_Circling_Serpentine.md` | Full technical reference for the extended module |

---

*Fraunhofer Institute · Electrochemistry Automation · June 2026*

