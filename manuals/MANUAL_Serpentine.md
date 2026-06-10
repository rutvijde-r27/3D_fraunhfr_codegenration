# Technical Manual — Serpentine Module

**Folder:** `Serpentine code & GUI/`  
**Files:** `gcode_generator.py` · `gcode_gui.py`  
**Version:** 2.0 · June 2026 · Fraunhofer Institute

---

## Table of Contents

1. [Module Purpose](#1-module-purpose)
2. [How to Run](#2-how-to-run)
3. [Input Parameters](#3-input-parameters)
4. [Scan Patterns](#4-scan-patterns)
5. [Coordinate System](#5-coordinate-system)
6. [Sub-Region Scanning](#6-sub-region-scanning)
7. [G-Code Structure](#7-g-code-structure)
8. [Skirting Sequence](#8-skirting-sequence)
9. [Validation Rules](#9-validation-rules)
10. [Safety Limits](#10-safety-limits)
11. [Output Files](#11-output-files)
12. [Calibration Utilities](#12-calibration-utilities)
13. [Constants](#13-constants)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Module Purpose

The Serpentine module generates G-code for three scan patterns: horizontal serpentine (X), vertical serpentine (Y), and diagonal zigzag. It is the original and most tested module in this project.

Use this module when:
- You need a clean back-and-forth raster scan over a rectangular plate area
- You want diagonal scanning at a specific angle
- You do not need circular or radial pre-conditioning

For circular paths combined with serpentine, use the **Circling and Serpentine** module instead.

---

## 2. How to Run

### GUI (Recommended)

```bash
cd "Serpentine code & GUI"
python gcode_gui.py
```

A CustomTkinter window opens. Fill in the fields, select a pattern from the dropdown, and click **Generate**. The output file path is shown in the window on success.

### CLI

```bash
cd "Serpentine code & GUI"
python gcode_generator.py
```

The program prompts for each parameter in sequence. Press Enter after each value. Press Enter on the line count prompt to accept the maximum.

---

## 3. Input Parameters

### Plate Width and Height

The physical dimensions of the electrochemical plate in millimetres.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm |
| Valid range | > 0 |
| Example | `100` × `100` |

---

### Scan Pattern

| Input | Pattern |
|---|---|
| `1` | Serpentine X — horizontal lines, step in Y |
| `2` | Serpentine Y — vertical lines, step in X |
| `3` | Diagonal — lines at a custom angle |

If `3` is selected, the angle prompt appears:

**Diagonal Angle**

| Property | Value |
|---|---|
| Type | Integer |
| Unit | degrees |
| Valid range | 0–179 |
| Example | `45` |

---

### Edge Offset

Distance from the plate edge to the start of the scan area. Applied equally on all four sides.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm |
| Valid range | ≥ 0, < half of smallest plate dimension |
| Example | `2` |

An edge offset of 2 mm on a 100 × 100 mm plate produces an active scan area of 96 × 96 mm.

---

### Sub-Region Width and Height

The actual area to be scanned. Must fit within the active area (plate minus edge offsets).

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm |
| Valid range | > 0, ≤ (plate dimension − 2 × offset) |
| Enter 0 | Uses the full active dimension |
| Example | `50` × `50` |

The sub-region is always centred within the active plate area automatically.

---

### Line Gap

Distance between adjacent scan lines.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm |
| Valid range | > 0, ≤ scan span in stepping direction |
| Example | `10` |

Smaller gap = denser coverage = more lines = longer scan time.

**Max lines formula:**
```
max_lines = floor(scan_span / gap) + 1
```

---

### Number of Lines

How many scan lines to generate.

| Property | Value |
|---|---|
| Type | Integer |
| Valid range | 1 to max_lines |
| Press Enter | Uses max_lines automatically |
| Example | `6` |

---

### Z-Depth

How far the probe descends during scanning. Negative values move downward.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm |
| Valid range | −13.0 ≤ value < 0 |
| Recommended | −10.0 to −11.0 |
| Example | `-11.0` |

**Z-Depth Reference:**

| Depth | Status | Notes |
|---|---|---|
| −9.0 mm | 🟢 Very safe | May not contact surface reliably |
| −10.0 mm | ✅ Recommended | Good default starting point |
| −11.0 mm | ✅ Recommended | Reliable contact |
| −12.0 mm | 🟡 Caution | Monitor closely |
| −12.6 mm | 🟡 Caution | Near limit |
| −13.0 mm | 🔴 Hard limit | Rejected by software |

---

### Speed

Probe movement speed during scan lines.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm/min |
| Valid range | 1–6000 |
| Recommended | 2400–3600 (40–60 mm/s) |
| Example | `3000` |

**Speed Reference:**

| mm/s | mm/min | Status |
|---|---|---|
| 20 | 1200 | 🟢 Very safe |
| 40 | 2400 | ✅ Recommended |
| 50 | 3000 | ✅ Recommended |
| 60 | 3600 | ✅ Recommended |
| 80 | 4800 | 🟡 Fast |
| 100 | 6000 | 🟡 Maximum |
| >100 | >6000 | 🔴 Blocked |

---

## 4. Scan Patterns

### Serpentine X

Lines run parallel to the X-axis. Direction alternates each line. Step axis is Y.

```
Line 1:  X_start ──────────────▶  X_end   (left to right)
Line 2:  X_end   ◀──────────────  X_start (right to left)
Line 3:  X_start ──────────────▶  X_end
...
```

**Algorithm:**
```python
y_positions = linspace(-sub_h/2, +sub_h/2, n_lines)
for i, y in enumerate(y_positions):
    x_from = -sub_w/2 if i % 2 == 0 else +sub_w/2
    x_to   = +sub_w/2 if i % 2 == 0 else -sub_w/2
    move(x_from, y) → scan to (x_to, y)
```

---

### Serpentine Y

Lines run parallel to the Y-axis. Direction alternates each line. Step axis is X.

```
Line 1:  Y_start ──▶ Y_end   (bottom to top)
Line 2:  Y_end   ──▶ Y_start (top to bottom)
Line 3:  Y_start ──▶ Y_end
...
```

**Algorithm:** Transpose of Serpentine X with X and Y roles swapped.

---

### Diagonal

Lines run at a user-specified angle θ. Each line is a chord through the sub-region; direction alternates for serpentine motion.

**Algorithm:**
```python
dir_vec  = (cos θ, sin θ)
perp_vec = (-sin θ, cos θ)

for i in range(n_lines):
    offset = (i - (n_lines-1)/2) × gap × perp_vec
    start  = offset - half_chord × dir_vec
    end    = offset + half_chord × dir_vec
    if i % 2 == 1: swap(start, end)
    move(start) → scan to (end)
```

`half_chord` is the half-diagonal of the sub-region bounding box, ensuring lines extend to full width.

---

## 5. Coordinate System

The origin (0, 0, 0) is the **plate centre**, established by running `homeZ12.gcode` once.

```
         +Y (away from operator)
          │
─── −X ───┼─── +X ───
          │
         −Y (toward operator)

Z = 0    → probe at calibrated home height
Z < 0    → probe descending toward plate
Z = −11  → typical scan depth
Z = −13  → hard limit, never reached
```

A 100 × 100 mm plate covers:
- X: −50 mm to +50 mm
- Y: −50 mm to +50 mm

With 2 mm edge offset, the active area is:
- X: −48 mm to +48 mm
- Y: −48 mm to +48 mm

---

## 6. Sub-Region Scanning

A sub-region restricts the scan to a portion of the active plate area. It is always centred:

```
active_w = plate_w - 2 × offset
active_h = plate_h - 2 × offset

sub_region:
  X: −sub_w/2  to  +sub_w/2
  Y: −sub_h/2  to  +sub_h/2

Margins:
  horizontal margin = (active_w − sub_w) / 2
  vertical margin   = (active_h − sub_h) / 2
```

The scan never touches the areas outside the sub-region.

---

## 7. G-Code Structure

Every generated file has this exact structure:

### Header

```gcode
; === SCAN FILE ===
; Generated: 2026-06-10 14:32:07
; Module: Serpentine
; Plate: 100.0 x 100.0 mm
; Pattern: Serpentine X
; Sub-region: 50.0 x 50.0 mm
; Edge offset: 2.0 mm | Gap: 10.0 mm | Lines: 6
; Z depth: -11.0 mm | Speed: 3000 mm/min
; ================
G21        ; mm units
G90        ; absolute positioning
G92 X0 Y0 Z0
```

### Skirting (2 loops)

```gcode
G0 F3000 Z2.0
G0 X-52.0 Y-52.0
G0 Z0.5
G1 F1200 X52.0 Y-52.0
G1 X52.0 Y52.0
G1 X-52.0 Y52.0
G1 X-52.0 Y-52.0
; (second loop at ±51 mm)
```

### Dwell

```gcode
G4 S90     ; 90-second pause
```

### Scan Block

```gcode
; Line 1
G0 Z2.0
G0 X-25.0 Y-10.0
G0 Z-11.0
G1 F3000 X25.0 Y-10.0
; Line 2
G0 Z2.0
G0 X25.0 Y0.0
G0 Z-11.0
G1 X-25.0 Y0.0
; ...
```

### Footer

```gcode
G0 Z2.0
G0 X0 Y0
M84        ; disable steppers
```

---

## 8. Skirting Sequence

Before every scan, two perimeter loops run at reduced speed (1200 mm/min):

**Loop 1:** ±52 mm from plate centre — outer perimeter  
**Loop 2:** ±51 mm from plate centre — inner perimeter

Purpose: prime the probe, displace surface debris, begin electrochemical equilibration.

After skirting, `G4 S90` inserts a 90-second pause. This is fixed and cannot be changed via the UI.

---

## 9. Validation Rules

| Parameter | Rule |
|---|---|
| Plate dimensions | > 0 |
| Edge offset | ≥ 0 and < half of smallest dimension |
| Sub-region | Fits within active area |
| Gap | > 0 and ≤ scan span |
| Line count | 1 to max_lines |
| Z-depth | −13.0 ≤ Z < 0 |
| Speed | 1 ≤ feedrate ≤ 6000 mm/min |
| Pattern | 1, 2, or 3 |
| Diagonal angle | 0–179° |

On failure: descriptive error shown, no file written, re-entry prompted.

---

## 10. Safety Limits

**Z hard limit: −13.0 mm** — Below this, mechanical contact with the plate holder is possible. Enforced as a code constant; cannot be bypassed via input.

**Speed hard limit: 6000 mm/min** — Above this, step loss is possible. Enforced as a code constant.

**Travel height: +2.0 mm** — The probe rises to Z = +2.0 mm between scan lines to prevent dragging across the surface.

---

## 11. Output Files

**Location:** `./gcode_output/` (created automatically if missing)

**Naming:** `scan_<pattern>_<W>x<H>_<YYYYMMDD_HHMMSS>.gcode`

Example: `scan_serpentineX_100x100_20260610_143207.gcode`

**Approximate file sizes:**

| Lines | Pattern | File size |
|---|---|---|
| 5 | Serpentine X | ~3 KB |
| 20 | Serpentine X | ~8 KB |
| 50 | Diagonal | ~18 KB |

---

## 12. Calibration Utilities

### homeZ12.gcode

Run once on the printer after mounting the plate:

```gcode
G28           ; Home all axes
G0 Z120       ; Raise Z
G0 X150 Y150  ; Move to bed centre
G92 X0 Y0 Z0  ; Set as origin
```

Re-run whenever the plate is re-mounted or the printer is homed by other means.

### z_home.py

```bash
python z_home.py    # Equivalent to G28 Z
```

### reset_xy.py

```bash
python reset_xy.py  # Equivalent to G28 X Y
```

### reset_z.py

```bash
python reset_z.py   # Equivalent to G28 Z (without moving XY)
```

---

## 13. Constants

| Constant | Value | Description |
|---|---|---|
| `Z_HARD_LIMIT` | −13.0 mm | Minimum Z-depth |
| `SPEED_MAX` | 6000 mm/min | Maximum feedrate |
| `TRAVEL_HEIGHT` | +2.0 mm | Z height between lines |
| `SKIRT_OUTER` | ±52 mm | Outer skirting loop radius |
| `SKIRT_INNER` | ±51 mm | Inner skirting loop radius |
| `SKIRT_SPEED` | 1200 mm/min | Skirting feedrate |
| `DWELL` | 90 seconds | Post-skirt pause |

---

## 14. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Gap too large error | Gap > scan span | Reduce gap or increase sub-region |
| Too many lines error | Lines > max | Reduce line count or gap |
| Z rejected | Value < −13.0 | Enter a less-negative value |
| Speed rejected | Value > 6000 | Enter ≤ 6000 mm/min |
| File not created | Missing write permission | Check `gcode_output/` is writable |
| Probe misses surface | Z not deep enough | Increment by −0.5 mm, re-test |
| Uneven line spacing | Plate not re-levelled | Re-run homeZ12.gcode after any mechanical change |

---

*For the Circling + Serpentine module, see `MANUAL_Circling_Serpentine.md`.*

*Fraunhofer Institute · June 2026*
