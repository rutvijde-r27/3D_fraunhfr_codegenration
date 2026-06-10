# 3D Fraunhofer G-Code Generator

> **Automated precision G-code for electrochemical plate scanning on a modified Anycubic Mega X 3D printer — developed at Fraunhofer Institute.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Printer](https://img.shields.io/badge/Printer-Anycubic%20Mega%20X-orange)]()
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()
[![Patterns](https://img.shields.io/badge/Patterns-Serpentine%20%7C%20Circling%20%7C%20Diagonal-purple)]()

---

## Overview

This tool generates precise movement paths (G-code) for scanning electrochemical plates with a modified Anycubic Mega X 3D printer. Instead of printing, the machine moves a probe across a plate surface in mathematically defined patterns at a controlled depth — fully automated, reproducible, and safe.

The project has grown into **two separate modules**, each with its own code and GUI:

| Module | Folder | What it does |
|---|---|---|
| **Serpentine** | `Serpentine code & GUI/` | Horizontal, vertical, and diagonal serpentine scan patterns |
| **Circling + Serpentine** | `Circling and Serpentine/` | Adds circular/perimeter scan paths combined with serpentine |

Both share the same printer setup and safety system.

---

## Quick Start

### Step 1 — Install Requirements

```bash
python --version        # Must be 3.10 or higher
pip install customtkinter
```

### Step 2 — One-Time Printer Calibration

Load `homeZ12.gcode` onto the printer and execute it **once** after mounting the plate:

```gcode
G28           ; Home all axes
G0 Z120       ; Raise Z to safe height
G0 X150 Y150  ; Move to physical bed center
G92 X0 Y0 Z0  ; Define this position as (0, 0, 0)
```

This sets the plate center as the coordinate origin for all subsequent G-code.

### Step 3 — Choose Your Module

**For serpentine-only patterns (Serpentine X, Y, Diagonal):**
```bash
cd "Serpentine code & GUI"
python gcode_gui.py          # GUI — recommended
python gcode_generator.py    # CLI — faster for experienced users
```

**For circling + serpentine combined patterns:**
```bash
cd "Circling and Serpentine"
python gcode_gui.py
python gcode_generator.py
```

### Step 4 — Enter Parameters

Both modules ask for the same core inputs:

| # | Input | Example |
|---|---|---|
| 1 | Plate size (W × H mm) | `100 × 100` |
| 2 | Scan pattern | `1` = Serpentine X |
| 3 | Edge offset (mm) | `2` |
| 4 | Sub-region size (mm) | `50 × 50` |
| 5 | Line gap (mm) | `10` |
| 6 | Number of lines | `6` (or Enter for max) |
| 7 | Z-depth (mm) | `-11.0` |
| 8 | Speed (mm/min) | `3000` |

The Circling + Serpentine module additionally asks for circling parameters (radius, number of loops).

### Step 5 — Load and Run

Your G-code file is saved to `./gcode_output/`. Load it onto the printer via SD card or serial and execute.

---

## Modules

### Serpentine Code & GUI

Located in `Serpentine code & GUI/`. The original and stable module.

**Patterns:**

```
Serpentine X          Serpentine Y          Diagonal (e.g. 45°)
→ → → → →            ↑ ↓ ↑ ↓ ↑            ↗ ↘ ↗ ↘
← ← ← ← ←            ↑ ↓ ↑ ↓ ↑            ↗ ↘ ↗ ↘
→ → → → →            ↑ ↓ ↑ ↓ ↑            ↗ ↘ ↗ ↘
```

- **Serpentine X** — Horizontal back-and-forth, stepping in Y
- **Serpentine Y** — Vertical up-and-down, stepping in X
- **Diagonal** — Zigzag at a custom angle (0–179°)

### Circling and Serpentine

Located in `Circling and Serpentine/`. Extended module that adds circular scan paths.

**What it adds:**
- Circular/perimeter scanning loops at configurable radii
- Combined sequences: circle first (to condition the surface), then serpentine scan
- Useful for experiments requiring radial symmetry or circular electrode geometries

---

## Scan Execution Flow

Every generated file — from both modules — follows this sequence:

```
① Skirting  →  ② Pause (90 s)  →  ③ Scan  →  ④ Return home

Skirting: 2 perimeter loops (±52 mm, ±51 mm)
          primes the probe and allows electrochemical settling

Pause:    90-second dwell — mandatory, always inserted automatically

Scan:     your chosen pattern at the configured Z-depth and speed

Return:   Z rises to +2 mm, XY moves to (0, 0)
```

---

## Safety Reference

### Z-Depth Limits

| Depth | Status | Notes |
|---|---|---|
| −9.0 mm | 🟢 Very safe | Shallow — use for initial tests |
| −10 to −11 mm | ✅ **Recommended** | Best balance of contact and safety |
| −12 to −12.6 mm | 🟡 Caution | Monitor closely |
| −13.0 mm | 🔴 **Hard limit** | Software will reject this value |

### Speed Limits

| mm/s | mm/min | Status |
|---|---|---|
| 20 | 1200 | 🟢 Very safe |
| 40–60 | 2400–3600 | ✅ **Recommended** |
| 80–100 | 4800–6000 | 🟡 Use carefully |
| > 100 | > 6000 | 🔴 **Blocked — not allowed** |

---

## Repository Structure

```
3D_fraunhfr_codegenration/
│
├── Serpentine code & GUI/          # Serpentine-only module (stable)
│   ├── gcode_generator.py          #   CLI generator
│   └── gcode_gui.py                #   GUI wizard (CustomTkinter)
│
├── Circling and Serpentine/        # Extended module: circles + serpentine
│   ├── gcode_generator.py          #   CLI generator
│   └── gcode_gui.py                #   GUI wizard
│
├── Initial run codes/              # Early prototypes and reference scripts
│
├── gcode_output/                   # All generated .gcode files (auto-created)
│
├── manuals/                        # Technical documentation
│   ├── MANUAL_Serpentine.md        #   Serpentine module manual
│   └── MANUAL_Circling_Serpentine.md  # Circling + Serpentine manual
│
├── homeZ12.gcode                   # One-time printer calibration
├── z_home.py                       # Z-axis homing utility
├── reset_xy.py                     # XY-axis reset utility
├── reset_z.py                      # Z-axis reset utility
│
├── README.md                       # This file
└── Introduction.md                 # Project background and motivation
```

---

## Common Issues

| Problem | Cause | Fix |
|---|---|---|
| `Gap too large` error | Gap > scan span | Use a smaller gap value |
| `Too many lines` error | Lines > max possible | Reduce line count or gap |
| Speed rejected | Feedrate > 6000 mm/min | Enter ≤ 6000 mm/min |
| Z rejected | Depth < −13.0 mm | Enter a less-negative value |
| No output file | Missing write permissions | Check `gcode_output/` is writable |
| Probe not reaching surface | Z not negative enough | Try −0.5 mm increments deeper |

---

## Machine Specifications

| Spec | Value |
|---|---|
| Printer | Anycubic Mega X (modified) |
| Bed size | 300 × 300 mm |
| Max speed | 100 mm/s / 6000 mm/min |
| Z working range | 0 to −13.0 mm |
| Z step resolution | 0.2 mm |
| Skirting pause | 90 seconds (fixed) |
| Coordinate origin | Plate center (set via homeZ12.gcode) |

---

## Documentation

| File | Purpose |
|---|---|
| `README.md` | This file — setup and quick start |
| `Introduction.md` | Project background and scientific context |
| `manuals/MANUAL_Serpentine.md` | Full technical reference for Serpentine module |
| `manuals/MANUAL_Circling_Serpentine.md` | Full technical reference for Circling + Serpentine module |

---

**Project:** Fraunhofer Institute — Electrochemistry Automation
**Language:** Python 3.10+  
**Version:** 2.0  
**Last Updated:** June 2026
