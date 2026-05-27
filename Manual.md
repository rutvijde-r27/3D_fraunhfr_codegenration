# 3D Fraunhofer GCode Generator — Technical Manual

A comprehensive technical guide and configuration manual for the Python utility designed to generate precision G-code motion paths for modified **Anycubic Mega X 3D printers** used in **electrochemistry applications** (Beschichtung).

---

## Table of Contents

1. [Environment Setup & Installation](#environment-setup--installation)
2. [How to Run the Application](#how-to-run-the-application)
3. [Calibration & Utility Scripts](#calibration--utility-scripts)
4. [Key Technical Concepts](#key-technical-concepts)
5. [Traversal Path Variations](#traversal-path-variations)
6. [System Fault Resolution](#system-fault-resolution)
7. [Fixed Hardware Profiles](#fixed-hardware-profiles)

---

## Environment Setup & Installation

Before running the generator, your computer must be properly configured with Python 3 and necessary dependencies.

### 1. Install Python 3

Ensure you have **Python 3.10 or newer** installed.

**Windows:**
- Download the latest installer from [python.org](https://python.org)
- ⚠️ **CRITICAL**: Check "Add Python.exe to PATH" during installation

**macOS / Linux:**
```bash
brew install python3
```

### 2. Install Required Dependencies

This project uses standard Python libraries (no external GUI required for CLI version).

```bash
pip install --upgrade pip
```

Optional: For future GUI version with CustomTkinter:
```bash
pip install customtkinter
```

### 3. Verify Installation

```bash
python --version
python -c "import pathlib; print('Pathlib OK')"
```

Expected output: `Python 3.10.x` or newer

---

## How to Run the Application

### Quick Start

1. **Open terminal/command prompt**

2. **Navigate to project directory:**
   ```bash
   cd /path/to/3D_fraunhofer_codegenration
   ```

3. **Run the main generator:**
   ```bash
   python gcode_generator.py
   ```

4. **Follow the 7 interactive prompts:**
   - Plate dimensions
   - Travel pattern
   - Edge offset for skirting
   - Sub-region (full or partial scan)
   - Gap between lines
   - Number of lines
   - Z-down working depth
   - Tool travel speed

5. **Output file** is saved to: `./gcode_output/scan_PATTERN_TIMESTAMP.gcode`

### Before First Run: Initialize Coordinate System

⚠️ **IMPORTANT**: Run this file **once** on your printer to set up the coordinate system:

```gcode
; homeZ12.gcode
G28           ; home to (0,0,0)
G0 Z120       ; move Z up 120 mm
G0 X150 Y150  ; move XY to center of 300mm bed
G92 X0 Y0 Z0  ; RESET — printer now thinks it's at (0,0,0)
```

After this, all generated GCode uses **logical coordinates** (relative to plate center).

---

## Calibration & Utility Scripts

Standalone automation utilities for system reset and calibration. Run directly from terminal:

### Reset Z Home (Safe Height)
```bash
python z_home.py
```
Sets the vertical safe baseline (Z = 0 mm position).

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

| Reference | Logical Coords | Physical Coords |
|-----------|---|---|
| Plate Center | (0, 0) | (150, 150) |
| Plate Front-Left | (-50, -50) | (100, 100) |
| Plate Back-Right | (+50, +50) | (200, 200) |
| Bed Minimum | (-150, -150) | (0, 0) |
| Bed Maximum | (+150, +150) | (300, 300) |

**Example:** 100×100 mm plate centered on machine:
- Logical X range: -50 to +50 mm
- Logical Y range: -50 to +50 mm
- Physical location: (100–200, 100–200) mm on 300×300 bed

---

### 2. Skirting Framework (Outer Boundary)

Before scanning, the tool executes a **preventative boundary rectangle** outside the plate to prime system alignment and settle the tool.

**Execution Sequence:**

```
1. Move to skirting corner (-52, -52)
2. Z down to working depth (-11 mm example)
3. Trace FIRST rectangle (±52 mm)
4. Z up to safe height (0 mm)
5. Move to inner skirting corner (-51, -51)
6. Z down to working depth
7. Trace SECOND rectangle (±51 mm)
8. Z up to safe height
9. PAUSE 90 seconds (for manual adjustment)
10. Begin scan lines
```

**Example Computation:**

Given a 100×100 mm plate with 2 mm edge offset:

```
Plate Boundaries:     ±50 X, ±50 Y
1st Skirting (outer): ±52 X, ±52 Y  (100 + 2×2 = 104 mm)
2nd Skirting (inner): ±51 X, ±51 Y  (100 + 2×1 = 102 mm)

Tool path (1st loop):
(-52, -52) → (52, -52) → (52, 52) → (-52, 52) → (-52, -52)
```

**Purpose:**
- Primes the electrochemistry system
- Settles tool alignment
- Allows operator 90 seconds to verify positioning before actual scan

---

### 3. Sub-Region Auto-Centering

When targeting partial plate areas, user dimensions are automatically **centered on the origin** to maintain equidistant margins on all four sides.

**Example Matrix:**

```
Full plate:     100 × 100 mm  (logical: -50 to +50 on both axes)
Sub-region:      50 × 50 mm  (user specifies size only)

Auto-calculated boundaries:
  X: -25 to +25 mm  (25 mm margin on left and right)
  Y: -25 to +25 mm  (25 mm margin on front and back)

Result: Equal margins on all 4 sides ✓
```

**Formula:**
```
Sub-region start X = -(sub_width / 2)
Sub-region start Y = -(sub_height / 2)
```

---

### 4. Line Density & Gap Intercepts

When a gap width (g) is declared across a sub-region span (S), the system calculates the absolute maximum possible passes:

```
N_max = floor(S / g) + 1
```

**Example:**

```
Sub-region height: 50 mm
Gap between lines: 10 mm

Lines possible = floor(50 / 10) + 1 = 6 lines

Program shows: "Maximum 6 lines possible"

If user enters > 6 → REJECTED with warning
If user enters ≤ 6 → ACCEPTED
```

---

### 5. Z-Down Working Constraints

**Operational Spectrum:**
- **Maximum Safety Height:** -9.0 mm (shallowest, safest)
- **Recommended Range:** -10.0 to -11.0 mm
- **Absolute Hard Limit:** -13.0 mm (tool touches plate surface)

**Increment Steps:** 0.2 mm (21 selectable options)

Available depths:
```
-9.0, -9.2, -9.4, -9.6, -9.8, -10.0, -10.2, -10.4, -10.6, -10.8,
-11.0, -11.2, -11.4, -11.6, -11.8, -12.0, -12.2, -12.4, -12.6, -12.8, -13.0
```

**Safety Rules:**
- ⚠️ Values < -13.0 mm → **HARD LIMIT** (machine won't accept)
- Tool will collide with plate if depth exceeds -13.0 mm
- Always use -10 to -11 mm for best results

---

## Traversal Path Variations

### Pattern 1: Serpentine X (Horizontal Lines)

Lines run **parallel to X-axis**, stepping forward in Y-direction.

```
Y=+25mm ⊢←─────────────⊣  line 6
Y=+15mm ⊢─────────────→⊣  line 5
Y=+5mm  ⊢←─────────────⊣  line 4
Y=-5mm  ⊢─────────────→⊣  line 3
Y=-15mm ⊢←─────────────⊣  line 2
Y=-25mm ⊢─────────────→⊣  line 1
        └──────────────┘
        X=-25  center  X=+25
```

**Use case:** Better for horizontal surface scanning (e.g., left-right electrochemistry coverage)

---

### Pattern 2: Serpentine Y (Vertical Lines)

Lines run **parallel to Y-axis**, stepping forward in X-direction.

```
X=-25  X=-15  X=-5   X=+5  X=+15  X=+25
  ↓      ↑      ↓      ↑     ↓      ↑
  │      │      │      │     │      │
  │      │      │      │     │      │
Y=+25 ──────────────────────────────────
  │      │      │      │     │      │
Y=0   ──────────────────────────────────
  │      │      │      │     │      │
Y=-25 ──────────────────────────────────
  ↑      ↓      ↑      ↓     ↑      ↓
```

**Use case:** Better for vertical surface scanning (e.g., front-back electrochemistry coverage)

---

### Pattern 3: Diagonal Serpentine

Lines traced at **custom angle** (e.g., 45°) with alternating direction zigzag.

```
45° angle example:
    ╱ ╲ ╱ ╲ ╱ ╲ 
   ╱   ╲ ╱   ╲ ╱
  ╱     ╲     ╲
```

**Use case:** Diagonal coverage patterns, combined X-Y scanning

**Calculation:**
- Angle (degrees): User specifies (0–179°)
- Lines perpendicular to angle at gap intervals
- Automatic clipping to sub-region boundaries

---

## System Fault Resolution

### Error: "Gap Too Large — No Lines Would Fit"

**Cause:** The gap value exceeds the total scanning span.

**Example:**
```
Pattern: Serpentine X (steps in Y)
Sub-region height: 50 mm
User gap: 60 mm

Gap (60) > Span (50) → Cannot fit even 1 line
```

**Resolution:** Enter a smaller gap value.

---

### Error: "Too Many Lines"

**Cause:** Line count exceeds mathematical ceiling for the sub-region.

**Example:**
```
Gap: 10 mm
Sub-region height: 50 mm
Maximum lines: 6
User input: 10 lines → REJECTED
```

**Resolution:** 
- Reduce line count to ≤ 6, OR
- Decrease gap to allow more lines

---

### Error: "Speed Exceeds Hardware Limit"

**Cause:** Feedrate input > 6000 mm/min (100 mm/s).

**Example:**
```
User entered: 7000 mm/min = 116.7 mm/s
Machine max:  6000 mm/min = 100 mm/s
```

**Resolution:** Enter feedrate ≤ 6000 mm/min (≤ 100 mm/s).

**Safe ranges:**
- Slow (safest): 20 mm/s (1200 mm/min)
- Recommended: 40–60 mm/s (2400–3600 mm/min)
- Fast (risky): 80–100 mm/s (4800–6000 mm/min)

---

### Error: "Z Exceeds Hard Limit"

**Cause:** Z-down depth < -13.0 mm (tool would collide with plate).

**Example:**
```
User entered: -13.5 mm
Hard limit:   -13.0 mm (surface contact)
```

**Resolution:** Enter Z-down ≥ -13.0 mm.

---

## Fixed Hardware Profiles

**Anycubic Mega X — Constant Specifications:**

| Hardware Property | Value | Notes |
|---|---|---|
| Physical Bed Size | 300 × 300 mm | Total available workspace |
| Logical Origin | (0, 0, 0) | Plate center |
| Physical Origin | (150, 150, 120) | After homeZ12.gcode |
| Safe Vertical Height | Z = 0 mm | No collision risk |
| Critical Collision Limit | Z = -13.0 mm | Hard limit (surface contact) |
| Maximum Feedrate | 6000 mm/min | 100 mm/s equivalent |
| Skirting Pause Duration | 90 seconds | G4 P90000 |
| Z Depth Increment | 0.2 mm | 21 selectable options |
| Skirting Loops | 2 passes | Outer (±offset) + Inner (±offset−1) |

---

## File Structure

```
3D_fraunhofer_codegenration/
├── gcode_generator.py           # Main program (CLI interactive)
├── homeZ12.gcode                # Coordinate system setup (run once)
├── z_home.py                    # Calibration utility
├── reset_xy.py                  # Calibration utility
├── reset_z.py                   # Calibration utility
├── gcode_output/                # Generated GCode files (created automatically)
│   └── scan_PATTERN_TIMESTAMP.gcode
├── README.md                    # Quick start guide
├── TECHNICAL_MANUAL.md          # This file
└── test_cases.md                # Test scenarios (optional)
```

---

## Workflow Summary

```
1. Run homeZ12.gcode (once, on printer)
   ↓
2. python gcode_generator.py
   ↓
3. Answer 7 interactive prompts
   ↓
4. GCode generated → ./gcode_output/
   ↓
5. Load onto printer
   ↓
6. Execute GCode:
   • Skirting: 2 loops (52×52, 51×51)
   • Pause: 90 seconds
   • Scan: User pattern (Serpentine X/Y/Diagonal)
   • Return: Z up, XY to origin
```

---

## Contact & Support

For issues or questions:
- Check [README.md](README.md) for quick start
- Review [test_cases.md](test_cases.md) for known scenarios
- Verify [Fixed Hardware Profiles](#fixed-hardware-profiles) section

---

**Version:** 1.0  
**Last Updated:** May 2026  
**Status:** Production Ready ✓
