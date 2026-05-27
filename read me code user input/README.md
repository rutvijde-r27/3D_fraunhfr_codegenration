# 3D Fraunhofer G-Code Generator

A Python-based utility designed to generate custom G-code motion paths for Anycubic 3D printers, specifically optimized for Fraunhofer co-generation patterns.

## 🚀 Features
* Automatically calculates grid parameters (`plate_x`, `plate_y`, `gap`, etc.).
* Supports multiple scanning patterns with dynamic angle adjustments.
* Generates an automatic preview of the first 15 motion lines in the terminal.
* Automatically creates an `output/` directory and saves structured `.gcode` files with clean timestamps.

## 🛠️ How it Works
Explain in a few sentences how the script runs. For example:
1. The script initializes configuration parameters for the print bed.
2. It processes the chosen geometric pattern and applies offsets or rotations.
3. It compiles the motion commands (`G0` and `G1`) into a single text block.
4. It exports the file directly to the `/output` folder.

## 📦 How to Run
1. Ensure you have Python installed.
2. Open your terminal in this directory and run:
   ```bash
   python gcode_generator.py or g code gen file 


# GCode Generator — Anycubic Mega X Electrochemistry

## What This Program Does

Generates **GCode** for **plate scanning** using an **Anycubic Mega X 3D printer** modified for **electrochemistry applications** (beschichtung).

The tool traces **serpentine or diagonal patterns** across a plate with full control over:
- **Plate dimensions** (any size)
- **Travel patterns** (Serpentine X, Serpentine Y, Diagonal)
- **Skirting boundary** (edge offset outside plate)
- **Sub-region scanning** (scan only part of plate, auto-centered)
- **Line spacing** (gap between parallel scan lines)
- **Working depth** (Z-down from -9 to -13 mm)
- **Tool speed** (20-100 mm/s)

---

## Setup: Before Using This Generator

### Run `homeZ12.gcode` Once

This file sets up your coordinate system:

```gcode
G28           ; home to (0,0,0)
G0 Z120       ; move Z up 120 mm
G0 X150 Y150  ; move XY to center of 300mm bed
G92 X0 Y0 Z0  ; RESET — printer now thinks it's at (0,0,0)
```

**After this:**
- Logical (0,0,0) = Physical (150, 150, 120)
- All generated GCode uses LOGICAL coordinates
- Printer translates them to PHYSICAL positions

---

## Key Concepts

### 1. Plate-Centered Coordinates

Your plate is **always centered** on the machine:

**Example: 100×100 mm plate**
```
Logical system (what you specify):
  Plate X: -50 to +50 mm  (center at 0)
  Plate Y: -50 to +50 mm  (center at 0)

Physical machine (300×300 bed):
  Bed X: 0 to 300 mm      (center at 150)
  Bed Y: 0 to 300 mm      (center at 150)

Mapping:
  Logical (0, 0)    → Physical (150, 150)  [plate center = machine center]
  Logical (-50, -50) → Physical (100, 100)  [plate front-left]
  Logical (+50, +50) → Physical (200, 200)  [plate back-right]
```

### 2. Skirting (Outside Boundary)

Tool **first traces a rectangle OUTSIDE your plate** (for priming/settling):

**Example: 100×100 plate + 2mm edge offset**
```
Plate boundaries:      ±50 X, ±50 Y  (100×100 mm)
Skirting boundaries:   ±52 X, ±52 Y  (104×104 mm)

Offset: 2 mm OUTSIDE the plate in all directions

Tool path:
  (-52, -52) → (52, -52) → (52, 52) → (-52, 52) → (-52, -52)
  ↑ front-left corner

After skirting:
  → Pauses 90 seconds (you can check alignment)
  → Z moves down to working depth
  → Starts scanning the actual region
```

### 3. Sub-Region Centering

You specify **size only** — it auto-centers:

**Example: 100×100 plate, scan 50×50 sub-region**
```
Full plate:         -50 to +50 (both X and Y)
Sub-region size:    50×50 (what you enter)
Auto-centered:
  X: -25 to +25     (margin: 25mm left/right)
  Y: -25 to +25     (margin: 25mm front/back)

Result: Equal margins on all 4 sides ✓
```

### 4. Gap & Line Calculation

When you enter a **gap** (distance between lines):

**Example: 50mm sub-region height, 10mm gap, Serpentine X**
```
Scan direction:  Y (height)
Available span:  50 mm
Gap:             10 mm

Lines that fit = floor(50 / 10) + 1 = 6 lines

Program calculates and shows:
  "Maximum lines possible: 6"
  
If you input > 6 lines → REJECTED with warning
If you input ≤ 6 lines → ACCEPTED
```

### 5. Z-Down Working Depth

Where the tool positions during scanning:

```
Range:        -9 mm (shallowest/safest) to -13 mm (hard limit)
Hard limit:   -13 mm (tool touches plate surface — CANNOT go deeper)
Recommended:  -10 to -11 mm
Increments:   0.1 mm or 0.2 mm (user selectable)

Input any value: -9, -10.5, -11.2, -12.9, etc.
Program warns if you exceed -13 mm.
```

### 6. Speed Input (Feedrate)

```
You enter:    Feedrate in mm/min  (e.g., 3000)
Program shows: Equivalent mm/s    (3000 ÷ 60 = 50 mm/s)
Machine limit: 100 mm/s = 6000 mm/min
Recommended:  40–60 mm/s (2400–3600 mm/min)

If feedrate > 6000 mm/min → Program warns (hard limit)
```

---

## Program Flow

### 7 Interactive Steps

| Step | Input | Example |
|------|-------|---------|
| 1 | Plate width × height | 100 × 100 mm |
| 2 | Pattern (1/2/3) | 1 = Serpentine X |
| 3 | Edge offset for skirting | 2 mm (outside plate) |
| 4 | Sub-region (full or partial) | Partial: 50 × 50 mm |
| 5 | Gap between lines | 10 mm |
| 5b | Number of lines | 6 (or fewer) |
| 6 | Z-down working depth | -11 mm |
| 7 | Feedrate | 3000 mm/min (= 50 mm/s) |

### Output GCode Sequence

Generated GCode does this, in order:

```
1. Header (configuration comments)
2. Move to skirting corner
3. PAUSE 90 seconds (for adjustment)
4. Z moves down to working depth
5. Trace 1 skirting rectangle (outside plate boundary)
6. Scan region using pattern:
   - Serpentine X: horizontal lines stepping in Y
   - Serpentine Y: vertical lines stepping in X
   - Diagonal: lines at an angle, zigzag
7. Z back to 0 (safe height)
8. Return to origin (0, 0, 0)
9. Disable motors
```

---

## Example Output GCode

**Configuration:**
- Plate: 100 × 100 mm
- Sub-region: 50 × 50 mm (centered)
- Pattern: Serpentine X (horizontal lines)
- Gap: 10 mm → 6 lines fit
- Edge offset: 2 mm → skirting is 104 × 104 mm
- Z working depth: -11 mm
- Feedrate: F3000 (50 mm/s)

**Generated GCode:**

```gcode
G21
G90
F3000

; SKIRTING PHASE
G0 X-52.0 Y-52.0      ; move to front-left corner of skirt
G4 P90000             ; pause 90 seconds
G0 Z-11.0             ; Z down to working depth
; skirting rectangle (outside plate)
G1 X52.0 Y-52.0       ; trace to front-right
G1 X52.0 Y52.0        ; trace to back-right
G1 X-52.0 Y52.0       ; trace to back-left
G1 X-52.0 Y-52.0      ; trace back to front-left

; SCAN PHASE (50×50 sub-region, centered)
; Lines are at Y = -25, -15, -5, 5, 15, 25 (6 lines, 10mm apart)
G0 X-25.0 Y-25.0      ; line 1 start (left side of sub-region)
G1 X25.0 Y-25.0       ; line 1 scan (move right) →

G0 X25.0 Y-15.0       ; line 2 start (right side)
G1 X-25.0 Y-15.0      ; line 2 scan (move left) ←

G0 X-25.0 Y-5.0       ; line 3 start (left side)
G1 X25.0 Y-5.0        ; line 3 scan (move right) →

G0 X25.0 Y5.0         ; line 4 start (right side)
G1 X-25.0 Y5.0        ; line 4 scan (move left) ←

G0 X-25.0 Y15.0       ; line 5 start (left side)
G1 X25.0 Y15.0        ; line 5 scan (move right) →

G0 X25.0 Y25.0        ; line 6 start (right side)
G1 X-25.0 Y25.0       ; line 6 scan (move left) ←

; END
G0 Z0                 ; move Z back to 0
G0 X0 Y0              ; return to center origin
M84 S0                ; disable motors
```

---

## Travel Patterns Explained

### Pattern 1: Serpentine X (Horizontal Lines)

```
Lines run LEFT-RIGHT along X axis
Each line steps UP one gap in Y direction

Y=+25mm ⊢←─────────────⊣  line 6
Y=+15mm ⊢─────────────→⊣  line 5
Y=+5mm  ⊢←─────────────⊣  line 4
Y=-5mm  ⊢─────────────→⊣  line 3
Y=-15mm ⊢←─────────────⊣  line 2
Y=-25mm ⊢─────────────→⊣  line 1
        └──────────────┘
        X=-25  center  X=+25

Why "serpentine"? Tool goes back-and-forth like a snake 🐍
```

### Pattern 2: Serpentine Y (Vertical Lines)

```
Lines run UP-DOWN along Y axis
Each line steps RIGHT one gap in X direction

                X=+25  X=+15  X=+5  X=-5  X=-15 X=-25
                  ↓      ↓      ↓     ↓     ↓      ↓
                  ↑      ↑      ↑     ↑     ↑      ↑
Y=+25         ────────────────────────────────────────
              │      │      │     │     │      │
Y=0           ────────────────────────────────────────
              │      │      │     │     │      │
Y=-25         ────────────────────────────────────────
                  ↑      ↑      ↑     ↑     ↑      ↑
                  ↓      ↓      ↓     ↓     ↓      ↓
```

### Pattern 3: Diagonal Serpentine

```
Lines at 45° angle (or user-specified angle)
Lines zigzag (alternate direction)

      ╱ ╲ ╱ ╲ ╱ ╲ 
     ╱   ╲ ╱   ╲ ╱
    ╱     ╲     ╲
```

---

## Troubleshooting

### Error: "Gap too large — no lines would fit"

**Cause:** The gap is bigger than the span the tool can step across.

**Example:**
```
Serpentine X: steps in Y direction
Scan height: 50 mm
Your gap: 60 mm

Can't fit even 1 line (60 > 50)
```

**Fix:** Enter a smaller gap.

---

### Error: "Too many lines"

**Cause:** You asked for more lines than physically fit.

**Example:**
```
Gap: 10 mm
Sub-region height: 50 mm
Max lines: 6
You entered: 10 lines → REJECTED
```

**Fix:** Enter ≤ 6 lines, or decrease the gap.

---

### Error: "Speed exceeds hardware limit"

**Cause:** Feedrate > 6000 mm/min (> 100 mm/s).

**Example:**
```
You entered: 7000 mm/min
Machine max: 6000 mm/min
```

**Fix:** Enter feedrate ≤ 6000 mm/min.

---

### Error: "Z exceeds hard limit"

**Cause:** Z-down < -13 mm (tool would touch/collide with plate).

**Fix:** Enter Z-down ≥ -13 mm.

---

## Machine Specifications (Built-in)

| Parameter | Value |
|-----------|-------|
| Bed size | 300 × 300 mm |
| Bed center | (150, 150) physical = (0, 0) logical |
| Logical Z zero | Z = 0 (safe height, no collision) |
| Logical Z hard limit | Z = -13 mm (tool touches surface) |
| Max speed | 100 mm/s (6000 mm/min) |
| Skirting pause time | 90 seconds |
| Z step increments | 0.1 mm or 0.2 mm |

---

## How to Use

### 1. Prepare Printer

Run `homeZ12.gcode` **once** to set up coordinates.

### 2. Run Generator

```bash
python3 gcode_generator.py
```

### 3. Answer 7 Questions

Follow prompts step-by-step.

### 4. Use Generated GCode

Output file: `gcode_output/scan_PATTERN_TIMESTAMP.gcode`

Load onto printer and execute.

---

## Files

- **gcode_generator.py** — Main Python program
- **homeZ12.gcode** — Setup file (run once before generating)
- **sample_output.gcode** — Example generated GCode
- **README.md** — This documentation
- **test_cases.md** — Test scenarios and failure modes

---

## Notes

✓ All coordinates are **LOGICAL** (centered on plate)
✓ Printer translates to **PHYSICAL** coordinates (bed 0–300)
✓ Z = 0 is **safe** (no collision)
✓ Z = -13 mm is **hard limit** (surface contact)
✓ After scan, tool **returns home** and stops
✓ Skirting gives you **90 seconds** to verify setup before scanning

---

**Ready to use!**
