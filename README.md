# GCode Generator — Anycubic Mega X Electrochemistry

**Generates precision G-code for electrochemistry plate scanning on modified Anycubic Mega X 3D printers.**

> 📖 For detailed technical information, see [TECHNICAL_MANUAL.md](TECHNICAL_MANUAL.md)

---

## ⚡ Quick Start (2 minutes)

### 1. Setup (One-Time Only)

Ensure Python 3.10+ is installed:
```bash
python --version
```

### 2. Initialize Printer (One-Time Only)

Load `homeZ12.gcode` onto your printer and execute once:
```gcode
G28
G0 Z120
G0 X150 Y150
G92 X0 Y0 Z0
```

### 3. Run Generator

**Choose one:**

**Option A: GUI Wizard** (easier)
```bash
python gcode_gui.py
```

**Option B: Interactive CLI**
```bash
python gcode_generator.py
```

### 4. Answer 7 Prompts

| Step | Input | Example |
|------|-------|---------|
| 1 | Plate size (W × H) | 100 × 100 mm |
| 2 | Pattern | 1 = Serpentine X |
| 3 | Edge offset | 2 mm |
| 4 | Sub-region | 50 × 50 mm |
| 5 | Gap | 10 mm |
| 5b | Lines | 6 (default = all) |
| 6 | Z depth | -11.0 mm |
| 7 | Speed | 3000 mm/min |

### 5. Load GCode

File: `./gcode_output/scan_*.gcode`

Load onto printer → Execute

---

## ✨ Features

✅ **Plate-Centered** — Logical (0,0) = plate center  
✅ **2-Loop Skirting** — Prime + settle before scan  
✅ **Auto-Centered Sub-Regions** — Equal margins all sides  
✅ **Smart Validation** — Calculates max lines automatically  
✅ **Z-Safety Limits** — Hard limit at -13.0 mm  
✅ **Speed Validation** — Max 100 mm/s (6000 mm/min)  
✅ **3 Patterns** — Serpentine X, Y, Diagonal  

---

## 📊 Patterns

**Serpentine X** — Horizontal lines (← →), step in Y  
**Serpentine Y** — Vertical lines (↑ ↓), step in X  
**Diagonal** — Custom angle zigzag (0–179°)  

---

## 🎯 Z-Depth Range

| Depth | Safety | Use |
|-------|--------|-----|
| -9.0 mm | 🟢 Very Safe | Maximum caution |
| -10 to -11 mm | 🟢 **Recommended** | Best results |
| -12 to -12.6 mm | 🟡 Fast | Monitor closely |
| -13.0 mm | 🔴 Hard Limit | **DO NOT EXCEED** |

---

## 🚀 Speed Recommendations

| Speed | Feedrate | Safety |
|-------|----------|--------|
| 20 mm/s | 1200 mm/min | 🟢 Very Safe |
| 40–60 mm/s | 2400–3600 mm/min | 🟢 **Recommended** |
| 80–100 mm/s | 4800–6000 mm/min | 🟡 Fast |
| > 100 mm/s | > 6000 mm/min | 🔴 **NOT ALLOWED** |

---

## 📁 File Structure

```
project/
├── gcode_generator.py          # CLI program
├── gcode_gui.py                # GUI wizard
├── homeZ12.gcode               # Setup (run once on printer)
├── z_home.py                   # Calibration tool
├── reset_xy.py                 # Calibration tool
├── reset_z.py                  # Calibration tool
├── gcode_output/               # Generated files (auto-created)
├── README.md                   # This file (quick start)
├── TECHNICAL_MANUAL.md         # Full documentation
└── test_cases.md               # Test scenarios
```

---

## ❌ Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Gap too large | Gap > scan span | Use smaller gap |
| Too many lines | Lines > max possible | Reduce lines or gap |
| Speed exceeds limit | Feedrate > 6000 mm/min | Use ≤ 6000 mm/min |
| Z exceeds limit | Z-down < -13.0 mm | Use Z ≥ -13.0 mm |

---

## 🔧 Machine Specs

| Spec | Value |
|------|-------|
| Bed Size | 300 × 300 mm |
| Max Speed | 100 mm/s (6000 mm/min) |
| Min Z Safe | 0 mm |
| Max Z Down | -13.0 mm (hard limit) |
| Skirting Pause | 90 seconds |
| Z Steps | 0.2 mm (21 options) |

---

## 📖 Documentation

- **Quick Start** → You are here
- **Full Technical Details** → [TECHNICAL_MANUAL.md](TECHNICAL_MANUAL.md)
- **Test Scenarios** → [test_cases.md](test_cases.md)

---

## 🎯 Typical Workflow

```
python gcode_generator.py
  ↓
Answer 7 prompts
  ↓
GCode → ./gcode_output/
  ↓
Load on printer
  ↓
Execute:
  1. Skirting: 2 loops (±52 mm, ±51 mm)
  2. Pause: 90 seconds
  3. Scan: Your pattern
  4. Return: Z up, XY home
```

---

**Status:** ✅ Production Ready  
**Version:** 1.0  
**Last Updated:** May 2026
