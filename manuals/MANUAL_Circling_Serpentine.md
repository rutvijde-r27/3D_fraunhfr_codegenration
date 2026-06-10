# Technical Manual — Circling and Serpentine Module

**Folder:** `Circling and Serpentine/`  
**Files:** `gcode_generator.py` · `gcode_gui.py`  
**Version:** 2.0 · June 2026 · Fraunhofer Institute

---

## Table of Contents

1. [Module Purpose](#1-module-purpose)
2. [When to Use This Module](#2-when-to-use-this-module)
3. [How to Run](#3-how-to-run)
4. [Input Parameters](#4-input-parameters)
5. [Circling Phase — How It Works](#5-circling-phase--how-it-works)
6. [Serpentine Phase — How It Works](#6-serpentine-phase--how-it-works)
7. [Combined Execution Sequence](#7-combined-execution-sequence)
8. [G-Code Structure](#8-g-code-structure)
9. [Coordinate System](#9-coordinate-system)
10. [Validation Rules](#10-validation-rules)
11. [Safety Limits](#11-safety-limits)
12. [Output Files](#12-output-files)
13. [Constants](#13-constants)
14. [Differences from Serpentine Module](#14-differences-from-serpentine-module)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Module Purpose

The **Circling and Serpentine** module extends the original Serpentine module by adding a **circular scanning phase** before the serpentine scan. The probe traces one or more concentric circular paths around the plate centre, then proceeds to a full serpentine scan.

This module was developed for experiments where:
- The electrochemical surface needs radial conditioning before linear scanning
- Circular electrode geometries require a matching probe path
- A combined radial + raster coverage is scientifically required

---

## 2. When to Use This Module

| Use case | Module |
|---|---|
| Standard raster scan only | **Serpentine code & GUI** |
| Raster scan + circular pre-conditioning | **Circling and Serpentine** ← this module |
| Circular geometry electrodes | **Circling and Serpentine** |
| Radial symmetry experiments | **Circling and Serpentine** |

If you only need serpentine patterns and do not require circular paths, use the **Serpentine code & GUI** module — it is simpler and faster to configure.

---

## 3. How to Run

### GUI

```bash
cd "Circling and Serpentine"
python gcode_gui.py
```

The GUI has two sections: **Circling Settings** and **Serpentine Settings**. Fill in both sections and click **Generate**.

### CLI

```bash
cd "Circling and Serpentine"
python gcode_generator.py
```

The program prompts for circling parameters first, then serpentine parameters.

---

## 4. Input Parameters

### Shared with Serpentine Module

The following parameters are identical to the Serpentine module (see `MANUAL_Serpentine.md` for full details):

| Parameter | Description |
|---|---|
| Plate width / height | Physical plate dimensions (mm) |
| Edge offset | Margin from plate edge (mm) |
| Sub-region width / height | Area to scan (mm) |
| Scan pattern | Serpentine X, Y, or Diagonal |
| Diagonal angle | Used only if Diagonal selected (0–179°) |
| Line gap | Distance between scan lines (mm) |
| Number of lines | How many scan lines (or Enter for max) |
| Z-depth | Probe scan depth (−13.0 to 0 mm) |
| Speed | Scan feedrate (1–6000 mm/min) |

---

### Circling-Specific Parameters

#### Circle Radius

The radius of the circular scan path, measured from the plate centre.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm |
| Valid range | > 0, ≤ (min(plate_w, plate_h) / 2 − edge_offset) |
| Example | `30` |

The circle must fit within the active scan area (plate minus edge offset).

---

#### Number of Circles

How many concentric circular loops to trace.

| Property | Value |
|---|---|
| Type | Integer |
| Valid range | ≥ 1 |
| Example | `3` |

If more than one circle is specified, circles are evenly spaced between the innermost radius and the outer radius. The spacing is:

```
circle_spacing = radius / n_circles
radii = [radius - (n_circles - 1 - i) × spacing  for i in range(n_circles)]
```

For example: radius = 30 mm, 3 circles → radii of 10, 20, 30 mm.

---

#### Circle Speed

Feedrate used during the circular paths. Can differ from the serpentine scan speed.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm/min |
| Valid range | 1–6000 |
| Recommended | 1200–2400 (slower than serpentine for conditioning) |
| Example | `1500` |

---

#### Circle Z-Depth

Z-depth used during the circular phase. Can differ from the serpentine Z-depth if needed.

| Property | Value |
|---|---|
| Type | Float |
| Unit | mm |
| Valid range | −13.0 ≤ value < 0 |
| Example | `-10.5` |

---

## 5. Circling Phase — How It Works

Circles are approximated as high-resolution polygons (typically 360 segments = 1° per step), which is indistinguishable from a true circle at the printer's positioning resolution.

**Algorithm for a single circle of radius r:**
```python
segments = 360
for i in range(segments + 1):
    angle = 2π × i / segments
    x = r × cos(angle)
    y = r × sin(angle)
    G1 to (x, y, z_circle)   # linear move along circle arc

# Close the circle by returning to start point
```

**For multiple concentric circles:**
```python
for r in radii:          # from innermost to outermost
    move to circle start point (r, 0)
    trace full circle at radius r
    lift Z to travel height
```

The probe starts each circle at angle 0 (positive X-axis direction from centre) and moves counter-clockwise.

---

## 6. Serpentine Phase — How It Works

The serpentine phase in this module is identical to the Serpentine module. After the circling phase completes, the probe lifts to travel height, moves to the serpentine scan start position, and executes the selected pattern.

See `MANUAL_Serpentine.md` → Section 4 for full algorithm details.

---

## 7. Combined Execution Sequence

```
① Skirting (2 perimeter loops)
      ↓
② Pause: 90 seconds
      ↓
③ Circling phase
      — innermost circle to outermost circle
      — probe at circle Z-depth
      — feedrate = circle speed
      ↓
④ Lift to travel height (+2.0 mm)
      ↓
⑤ Serpentine scan phase
      — probe at serpentine Z-depth
      — feedrate = scan speed
      ↓
⑥ Lift to travel height
      ↓
⑦ Return to (0, 0) — motors disabled
```

The two Z-depths (circle and serpentine) are independent. If they are the same value, no Z change occurs at the transition.

---

## 8. G-Code Structure

### Header

```gcode
; === SCAN FILE ===
; Generated: 2026-06-10 14:45:00
; Module: Circling + Serpentine
; Plate: 100.0 x 100.0 mm
; Circles: 3 @ radius 30 mm | Circle Z: -10.5 mm | Circle speed: 1500 mm/min
; Pattern: Serpentine X | Sub-region: 50.0 x 50.0 mm
; Gap: 10.0 mm | Lines: 6 | Z depth: -11.0 mm | Speed: 3000 mm/min
; ================
G21
G90
G92 X0 Y0 Z0
```

### Skirting Block

Identical to Serpentine module — two perimeter loops at ±52 mm and ±51 mm.

### Dwell

```gcode
G4 S90
```

### Circling Block

```gcode
; --- Circle 1 of 3 (radius: 10.0 mm) ---
G0 Z2.0
G0 X10.0 Y0.0
G0 Z-10.5
G1 F1500 X9.985 Y0.873    ; arc segment 1°
G1 X9.939 Y1.743          ; arc segment 2°
; ... 360 segments total
G1 X10.0 Y0.0             ; close circle

; --- Circle 2 of 3 (radius: 20.0 mm) ---
G0 Z2.0
G0 X20.0 Y0.0
G0 Z-10.5
; ... 360 segments
```

### Serpentine Block

```gcode
; --- Serpentine X scan ---
G0 Z2.0
G0 X-25.0 Y-10.0
G0 Z-11.0
G1 F3000 X25.0 Y-10.0
; ...
```

### Footer

```gcode
G0 Z2.0
G0 X0 Y0
M84
```

---

## 9. Coordinate System

Identical to the Serpentine module. Origin (0, 0, 0) = plate centre, set by `homeZ12.gcode`.

The circling phase uses the same coordinate system. Circles are centred on (0, 0) — the plate centre.

---

## 10. Validation Rules

All Serpentine module validations apply, plus:

| Parameter | Rule |
|---|---|
| Circle radius | > 0 and fits within active area |
| Number of circles | ≥ 1 |
| Circle speed | 1–6000 mm/min |
| Circle Z-depth | −13.0 ≤ value < 0 |

The circle must fit entirely within the plate's active area. The software checks:
```
radius ≤ min(active_width, active_height) / 2
```

---

## 11. Safety Limits

All Serpentine module safety limits apply to both phases:

| Limit | Value | Applies to |
|---|---|---|
| Z hard limit | −13.0 mm | Both circle and serpentine Z-depths |
| Speed limit | 6000 mm/min | Both circle and serpentine speeds |
| Travel height | +2.0 mm | Between all moves |

---

## 12. Output Files

**Location:** `./gcode_output/` (auto-created)

**Naming:** `scan_circling_serp_<W>x<H>_<YYYYMMDD_HHMMSS>.gcode`

Example: `scan_circling_serp_100x100_20260610_144500.gcode`

**Approximate sizes:** Larger than Serpentine-only files due to the 360 arc segments per circle.

| Circles | Serp. lines | Approx. size |
|---|---|---|
| 1 circle | 6 lines | ~20 KB |
| 3 circles | 6 lines | ~40 KB |
| 3 circles | 20 lines | ~50 KB |

---

## 13. Constants

Shared constants (same as Serpentine module):

| Constant | Value |
|---|---|
| `Z_HARD_LIMIT` | −13.0 mm |
| `SPEED_MAX` | 6000 mm/min |
| `TRAVEL_HEIGHT` | +2.0 mm |
| `SKIRT_OUTER` | ±52 mm |
| `SKIRT_INNER` | ±51 mm |
| `SKIRT_SPEED` | 1200 mm/min |
| `DWELL` | 90 seconds |

Circling-specific constants:

| Constant | Value | Description |
|---|---|---|
| `CIRCLE_SEGMENTS` | 360 | Arc resolution (1° per segment) |
| `CIRCLE_START_ANGLE` | 0° | Circles begin at positive X axis |
| `CIRCLE_DIRECTION` | Counter-clockwise | Fixed |

---

## 14. Differences from Serpentine Module

| Feature | Serpentine module | Circling + Serpentine module |
|---|---|---|
| Scan phases | Serpentine only | Circling → Serpentine |
| Circle parameters | Not present | Radius, count, speed, Z |
| Output file size | Small | Larger (arc segments) |
| Execution time | Shorter | Longer (circles add travel) |
| Use case | Standard raster scan | Radial conditioning + raster |
| GUI sections | Single | Two: Circling + Serpentine |

Both modules share: printer setup, calibration files, skirting, pause, safety limits, coordinate system, and output folder.

---

## 15. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Circle radius rejected | Radius > active area half-width | Reduce radius or edge offset |
| Circle not closing cleanly | Floating point at segment join | Expected — imperceptible at printer resolution |
| File much larger than expected | Many circles × 360 segments | Normal — reduce circle count if size is a concern |
| Serpentine not executing after circles | Z not lifting between phases | Check travel height constant in code |
| Gap / line errors | Same as Serpentine module | See `MANUAL_Serpentine.md` §14 |
| Z or speed rejected | Same limits apply | Same fix as Serpentine module |

---

*For the serpentine-only module, see `MANUAL_Serpentine.md`.*  
*For project background, see `Introduction.md`.*

*Fraunhofer Institute · June 2026*
