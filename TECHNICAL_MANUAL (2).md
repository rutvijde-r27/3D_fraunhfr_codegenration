# 3D Fraunhofer GCode Generator — Technical Manual

A comprehensive technical guide and configuration manual for the Python utility designed to generate precision G-code motion paths for modified **Anycubic Mega X 3D printers** used in **electrochemistry applications** (Beschichtung).

---

## Table of Contents

1. [Environment Setup & Installation](#environment-setup--installation)
2. [How to Run the Application](#how-to-run-the-application)
3. [Before First Run: Initialize Coordinate System](#before-first-run-initialize-coordinate-system)
4. [How to Operate the Wizard GUI](#how-to-operate-the-wizard-gui)
5. [Calibration & Utility Scripts](#calibration--utility-scripts)
6. [Key Technical Concepts](#key-technical-concepts)
7. [Traversal Path Variations](#traversal-path-variations)
8. [System Fault Resolution](#system-fault-resolution)
9. [Fixed Hardware Profiles](#fixed-hardware-profiles)
10. [File Structure](#file-structure)

---

## Environment Setup & Installation

Before running the generator, your computer must be properly configured with **Python 3** and the necessary **Tkinter graphical frameworks**.

### 1. Install Python 3

Ensure you have **Python 3.10 or newer** installed.

**Windows:**
- Download the latest installer from [python.org](https://python.org)
- ⚠️ **CRITICAL**: Check **"Add Python.exe to PATH"** during installation

**macOS / Linux:**
```bash
brew install python3
```

### 2. Verify Base Tkinter Installation

**Tkinter comes pre-installed** with standard Python distributions on Windows. You can verify your system's core Tkinter backend by running this command in your terminal:

```bash
python -m tkinter
```

**Expected result:** A small blank test window pops up → Your system's native Tkinter installation is healthy and active.

### 3. Install Modern Tkinter UI Extensions

This project utilizes **CustomTkinter**, an advanced styling framework built directly on top of Python's native Tkinter library to provide:
- Clean dark theme UI
- Consistent font scaling
- Modern layout managers
- Professional appearance

Install CustomTkinter:

```bash
pip install --upgrade pip
pip install customtkinter
```

### 4. Verify Full GUI Environment

```bash
python --version
python -c "import customtkinter; print('Tkinter / CustomTkinter UI Engine OK')"
```

**Expected output:** 
```
Python 3.10.x (or newer)
Tkinter / CustomTkinter UI Engine OK
```

---

## How to Run the Application

The utility supports **two operational interfaces**:
- **GUI Wizard** (gcode_gui.py) — Interactive graphical setup with CustomTkinter
- **CLI** (gcode_generator.py) — Command-line interactive terminal interface

### Option A: Running the Tkinter Setup Wizard (GUI)

The graphical interface provides a modern, user-friendly wizard with 5 progressive validation steps.

**Standard Python Environment:**

```bash
cd /path/to/project/directory
python gcode_gui.py
```

Replace `/path/to/project/directory` with your actual project folder path.

**Anaconda Environment** (If using conda):

If your packages are isolated within Anaconda, activate your environment first so the script can access your installed Tkinter and CustomTkinter libraries natively:

```bash
conda activate your-environment-name
cd /path/to/project/directory
python gcode_gui.py
```

Replace `your-environment-name` with your actual conda environment name and `/path/to/project/directory` with your project folder.

**Expected Result:** A modern dark-themed GUI window opens with the 5-step wizard interface.

### Option B: Running the Interactive Command Line Interface (CLI)

For users who prefer terminal-based interaction, the CLI version provides the same functionality through sequential prompts:

```bash
cd /path/to/project/directory
python gcode_generator.py
```

Replace `/path/to/project/directory` with your actual project folder path.

**Expected Result:** 7 sequential interactive keyboard prompts appear in your terminal console. Answer each prompt to generate your GCode file.

### Which Should I Choose?

| Interface | Best For | Advantage |
|-----------|----------|-----------|
| **GUI (gcode_gui.py)** | Visual users, first-time users | Easy navigation, visual validation, back/next buttons |
| **CLI (gcode_generator.py)** | Terminal users, scripting | Fast, lightweight, no dependencies beyond Tkinter |

Both produce identical GCode output. Choose whichever you're most comfortable with.

---

## Before First Run: Initialize Coordinate System

⚠️ **IMPORTANT**: Run this file **once** on your printer before executing production scans to sync the zero points:

**File: `homeZ12.gcode`**

```gcode
G28           ; home to absolute physical (0,0,0)
G0 Z120       ; move Z up 120 mm
G0 X150 Y150  ; move XY to center of 300mm bed
G92 X0 Y0 Z0  ; RESET — printer sets current location as logical (0,0,0)
```

After running this, all generated GCode uses **logical coordinates** (relative to plate center). The machine automatically translates them to physical positions.

---

## How to Operate the Wizard GUI

The graphical interface is broken down into **5 progressive validation steps** to prevent incorrect variables from crashing the system.

**Navigation Flow:**
```
[Step 1: Base Dimensions] 
    ↓ Next
[Step 2: Scan Target] 
    ↓ Next
[Step 3: Line Spacing] 
    ↓ Next
[Step 4: Speed & Depth] 
    ↓ Next
[Step 5: Verification & Execute]
```

Use the **Next** and **Back** buttons to navigate between screens.

### Step 1: Base Plate Dimensions

**Inputs:**
- **Plate Width (mm)** — Physical plate width dimension
- **Plate Height (mm)** — Physical plate height dimension
- **Edge Offset (mm)** — Distance outside plate boundary for skirting
  - Range: 0.0 to 10.0 mm
  - Example: 2 mm offset on 100×100 plate = 104×104 skirting rectangle

### Step 2: Scan Target Setup

**Scan Style Menu (choose one):**
- **Serpentine X** — Horizontal sweeps (← →)
- **Serpentine Y** — Vertical sweeps (↑ ↓)
- **Diagonal** — Custom angle sweeps

**Angle Input (visible only for Diagonal):**
- Range: 0–179 degrees
- Sets the rotation vector relative to horizontal frame

**Scan Entire Plate Area Checkbox:**
- **✓ Checked** — Tool scans full plate dimensions (from Step 1)
- **☐ Unchecked** — Define custom sub-region with:
  - Sub Width (mm)
  - Sub Height (mm)
  - *(Auto-centered on plate)*

### Step 3: Spacing & Line Density

**Line Gap (mm):**
- Distance between consecutive scan lines
- Example: 10 mm gap on 50 mm region = 6 lines maximum

**Recalculate Bounds Button:**
- Click after changing gap parameter
- System computes maximum lines dynamically
- Displays statistics in info box

**Line Count to Run:**
- Enter custom integer (number of scan lines)
- Leave blank = automatically use maximum safe capacity

### Step 4: Tool Depth & Velocity Profiles

**Z-Depth Profile (Dropdown Menu):**
- Select exact immersion layer depth
- Available steps: **-9.0 mm to -13.0 mm** in **0.2 mm increments**
- 21 total options: -9.0, -9.2, -9.4, ... -12.8, -13.0
- Recommended: -10.0 to -11.0 mm

**Feedrate Speed (mm/min):**
- Sets toolhead linear motion travel rate
- Machine governor clamps inputs automatically
- **Hard limit: 6000 mm/min** (100 mm/s)
- Recommended: 2400–3600 mm/min (40–60 mm/s)

### Step 5: Execute System Sequence Verification

**Review Terminal Manifest:**
- Non-editable display showing:
  - Plate area configuration
  - Track spacing parameters
  - Tool immersion metrics
  - Feedrate values
  - Skirting boundaries

**Generate File Execution:**
- Click final button in right corner
- Modal dialog confirms save completion
- Displays absolute file path: `./gcode_output/scan_*.gcode`
- File is ready for machine loading

---

## Calibration & Utility Scripts

Standalone automation utilities for system reset and calibration. Run directly from terminal:

### Reset Z Home (Safe Height)

```bash
python z_home.py
```

Sets the vertical safe baseline position (Z = 0 mm).

### Reset XY Coordinates

```bash
python reset_xy.py
```

Returns horizontal tool head positioning to logical zero (X = 0, Y = 0).

### Reset Z Configuration

```bash
python reset_z.py
```

Readjusts the deep vertical plane settings for electrochemistry depth.

---

## Key Technical Concepts

### 1. Plate-Centered Coordinate System

The software uses a **Logical Coordinate System** centered on the target plate. The machine automatically maps these relative inputs onto absolute hardware boundaries.

```
Logical Base (0,0) ──→ Physical Bed Center (150, 150)
```

**Coordinate Mapping Framework (300×300 mm Bed):**

| Reference | Logical Coords | Physical Coords | Notes |
|-----------|---|---|---|
| Plate Center | (0, 0) | (150, 150) | Origin |
| Plate Front-Left | (-50, -50) | (100, 100) | Corner |
| Plate Back-Right | (+50, +50) | (200, 200) | Corner |
| Bed Minimum | (-150, -150) | (0, 0) | Hardware limit |
| Bed Maximum | (+150, +150) | (300, 300) | Hardware limit |

**Example:** 100×100 mm plate centered on machine:
```
Logical X range:  -50 to +50 mm
Logical Y range:  -50 to +50 mm
Physical location: (100–200, 100–200) mm on 300×300 bed
```

---

### 2. Skirting Framework (Outer Boundary)

Before scanning, the tool executes a **preventative boundary rectangle** outside the plate to prime system alignment and settle the tool.

**Two-Loop Execution Sequence:**

```
1. Move to outer skirting corner (-52, -52)      [rapid move]
2. Z down to working depth (-11.0 mm example)    [immerse]
3. Trace FIRST rectangle (±52 mm)                [prime loop 1]
4. Z up to safe height (0 mm)                    [retract]

5. Move to inner skirting corner (-51, -51)      [rapid move]
6. Z down to working depth (-11.0 mm)            [immerse]
7. Trace SECOND rectangle (±51 mm)               [settle loop 2]
8. Z up to safe height (0 mm)                    [retract]

9. PAUSE 90 seconds                              [manual adjustment]
10. Begin actual scan lines
```

**Example Computation:**

Given a 100×100 mm plate with 2 mm edge offset:

```
Plate Boundaries:     ±50 X, ±50 Y
1st Skirting (outer): ±52 X, ±52 Y  (100 + 2×2 = 104 mm)
2nd Skirting (inner): ±51 X, ±51 Y  (100 + 2×1 = 102 mm)
```

---

### 3. Sub-Region Auto-Centering

When targeting **partial plate areas**, user dimensions are automatically **centered on the origin** to maintain equidistant margins on all four sides.

**Formula:**
```
Sub-region start X = -(sub_width / 2)
Sub-region start Y = -(sub_height / 2)
```

**Example:**
```
Full plate:     100 × 100 mm
Sub-region:      50 × 50 mm

Auto-centered:
  X: -25 to +25 mm  (25 mm margin each side)
  Y: -25 to +25 mm  (25 mm margin each side)
```

---

### 4. Line Density & Gap Intercepts

When a gap width (g) is declared across a sub-region span (S), the system calculates:

```
N_max = floor(S / g) + 1
```

**Example:**
```
Sub-region height: 50 mm
Gap: 10 mm

Maximum lines = floor(50 / 10) + 1 = 6 lines
```

---

### 5. Z-Down Working Constraints

**Operational Spectrum:**

| Depth | Classification | Use |
|-------|---|---|
| -9.0 mm | 🟢 Maximum safety | Very conservative |
| -10.0 to -11.0 mm | 🟢 Recommended | Best results |
| -12.0 to -12.6 mm | 🟡 Fast | Monitor carefully |
| -13.0 mm | 🔴 Hard limit | **DO NOT EXCEED** |

---

## Traversal Path Variations

### Pattern 1: Serpentine X (Horizontal Lines)

Lines run **parallel to X-axis**, stepping in Y-direction.

```
Y=+25mm ⊢←─────────────⊣  line 6
Y=+15mm ⊢─────────────→⊣  line 5
Y=+5mm  ⊢←─────────────⊣  line 4
Y=-5mm  ⊢─────────────→⊣  line 3
Y=-15mm ⊢←─────────────⊣  line 2
Y=-25mm ⊢─────────────→⊣  line 1
```

### Pattern 2: Serpentine Y (Vertical Lines)

Lines run **parallel to Y-axis**, stepping in X-direction.

```
X=-25  X=-15  X=-5   X=+5  X=+15  X=+25
  ↓      ↑      ↓      ↑     ↓      ↑
Y=+25 ──────────────────────────────────
Y=0   ──────────────────────────────────
Y=-25 ──────────────────────────────────
  ↑      ↓      ↑      ↓     ↑      ↓
```

### Pattern 3: Diagonal Serpentine

Lines at **custom angle** (0–179°) with **alternating zigzag**.

```
45° example:
    ╱ ╲ ╱ ╲ ╱ ╲
```

---

## System Fault Resolution

### Error: "Gap Too Large"

**Cause:** Gap value exceeds scanning span.

**Fix:** Use smaller gap.

### Error: "Too Many Lines"

**Cause:** Line count exceeds maximum.

**Fix:** Reduce lines or decrease gap.

### Error: "Speed Exceeds Limit"

**Cause:** Feedrate > 6000 mm/min.

**Fix:** Use ≤ 6000 mm/min (≤ 100 mm/s).

### Error: "Z Exceeds Hard Limit"

**Cause:** Z-down < -13.0 mm.

**Fix:** Use Z ≥ -13.0 mm.

---

## Fixed Hardware Profiles

**Anycubic Mega X — Constant Specifications:**

| Property | Value | Notes |
|----------|-------|-------|
| Bed Size | 300 × 300 mm | Workspace |
| Logical Origin | (0, 0, 0) | Plate center |
| Physical Origin | (150, 150, 120) | After homeZ12.gcode |
| Safe Z Height | Z = 0 mm | No collision |
| Hard Z Limit | Z = -13.0 mm | Surface contact |
| Max Feedrate | 6000 mm/min | 100 mm/s |
| Skirting Pause | 90 seconds | G4 P90000 |
| Z Increment | 0.2 mm | 21 options |
| Skirting Loops | 2 passes | Outer + Inner |

---

## File Structure

```
3D_fraunhofer_codegenration/
├── gcode_generator.py           # CLI main program
├── gcode_gui.py                 # GUI wizard
├── homeZ12.gcode                # Setup file
├── z_home.py                    # Calibration tool
├── reset_xy.py                  # Calibration tool
├── reset_z.py                   # Calibration tool
├── gcode_output/                # Generated files
├── README.md                    # Quick start
├── TECHNICAL_MANUAL.md          # This file
└── test_cases.md                # Test scenarios
```

---

**Version:** 1.0  
**Status:** ✅ Production Ready  
**Last Updated:** May 2026
