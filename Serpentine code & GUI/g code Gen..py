#!/usr/bin/env python3
"""
GCode Generator — Anycubic Mega X Electrochemistry
Plate-centered coordinates
Skirting outside plate boundary
Z-depth: -9 to -13 mm with 0.2mm increments (21 options)
Sub-region auto-centered on plate
"""
from __future__ import annotations
import math, sys
from pathlib import Path
from datetime import datetime

# ════════════════════════════════════════════════════════════════════════════
#  MACHINE CONSTANTS
# ════════════════════════════════════════════════════════════════════════════

# After homeZ12.gcode: logical (0,0,0) = physical (150, 150, 120)
LOGICAL_ORIGIN_X = 150  # mm
LOGICAL_ORIGIN_Y = 150  # mm
LOGICAL_ORIGIN_Z = 120  # mm

MEGA_X_BUILD_X = 300
MEGA_X_BUILD_Y = 300
MEGA_X_MAX_MMS = 100

# Z-down limits
Z_DOWN_MAX = -9.0      # shallowest
Z_DOWN_HARD_LIMIT = -13.0  # absolute limit

# Skirting
SKIRT_DWELL_S = 90  # seconds
SKIRT_PASSES = 1    # one pass around periphery

# Output folder for generated GCode files
OUTPUT_FOLDER = Path(__file__).parent.resolve() / "output"


# ════════════════════════════════════════════════════════════════════════════
#  VISUAL HELPERS
# ════════════════════════════════════════════════════════════════════════════

W = 64

def box_top(title="", icon="✦"):
    t = f"  {icon}  {title}"
    print(f"  ╔{'═'*W}╗")
    print(f"  ║{t:<{W+2}}║")
    print(f"  ╠{'═'*W}╣")

def box_row(text=""):
    print(f"  ║  {text:<{W}}║")

def box_bot():
    print(f"  ╚{'═'*W}╝")

def info_box(title, rows):
    box_top(title, "✦")
    for r in rows: box_row(r)
    box_bot()

def warn_box(title, rows):
    box_top(title, "✗")
    for r in rows: box_row(r)
    box_bot()

def ok_box(title, rows):
    box_top(title, "✓")
    for r in rows: box_row(r)
    box_bot()

def sep(c="─", w=68): print(c * w)


# ════════════════════════════════════════════════════════════════════════════
#  INPUT HELPERS
# ════════════════════════════════════════════════════════════════════════════

def prompt_float(msg, *, allow_zero=False, min_val=0.0, max_val=None):
    while True:
        raw = input(msg).strip().replace(",", ".")
        try:
            v = float(raw)
            if allow_zero and v < min_val:
                print(f"  ✗  Must be ≥ {min_val}."); continue
            if not allow_zero and v <= min_val:
                print(f"  ✗  Must be > {min_val}."); continue
            if max_val is not None and v > max_val:
                print(f"  ✗  Must be ≤ {max_val}."); continue
            return v
        except ValueError:
            print("  ✗  Please enter a valid number.")

def prompt_int(msg, *, choices=None, min_val=1):
    while True:
        raw = input(msg).strip()
        try:
            v = int(raw)
            if choices and v not in choices:
                print(f"  ✗  Choose one of: {choices}"); continue
            if v < min_val:
                print(f"  ✗  Must be ≥ {min_val}."); continue
            return v
        except ValueError:
            print("  ✗  Enter a whole number.")

def prompt_yes_no(msg):
    while True:
        r = input(f"{msg} [y/n]: ").strip().lower()
        if r in ("y","yes"): return True
        if r in ("n","no"):  return False
        print("  ✗  Enter y or n.")


# ════════════════════════════════════════════════════════════════════════════
#  GEOMETRY
# ════════════════════════════════════════════════════════════════════════════

def max_lines_possible(sw, sh, pattern, gap, angle_deg=45.0):
    if pattern == 1:   span = sh
    elif pattern == 2: span = sw
    else:              span = abs(sw*math.sin(math.radians(angle_deg))) + abs(sh*math.cos(math.radians(angle_deg)))
    return max(1, int(span / gap) + 1)

def gap_fits(sw, sh, pattern, gap, angle_deg=45.0):
    if pattern == 1:   return gap <= sh
    elif pattern == 2: return gap <= sw
    else:              return gap <= (abs(sw*math.sin(math.radians(angle_deg))) + abs(sh*math.cos(math.radians(angle_deg))))

def f(n, d=4): return round(n, d)

def clip_line(x1,y1,x2,y2,xn,xx,yn,yx):
    I,L,R,B,T=0,1,2,4,8
    def reg(x,y):
        c=0
        if x<xn: c|=L
        elif x>xx: c|=R
        if y<yn: c|=B
        elif y>yx: c|=T
        return c
    c1,c2=reg(x1,y1),reg(x2,y2)
    for _ in range(20):
        if not(c1|c2): return (x1,y1),(x2,y2)
        if c1&c2: return None,None
        co=c1 or c2
        if co&T:   x=x1+(x2-x1)*(yx-y1)/(y2-y1) if y2!=y1 else x1; y=yx
        elif co&B: x=x1+(x2-x1)*(yn-y1)/(y2-y1) if y2!=y1 else x1; y=yn
        elif co&R: y=y1+(y2-y1)*(xx-x1)/(x2-x1) if x2!=x1 else y1; x=xx
        else:      y=y1+(y2-y1)*(xn-x1)/(x2-x1) if x2!=x1 else y1; x=xn
        if co==c1: x1,y1,c1=x,y,reg(x,y)
        else:      x2,y2,c2=x,y,reg(x,y)
    return None,None


# ════════════════════════════════════════════════════════════════════════════
#  GCODE BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def gc_header(cfg):
    pat_names = {1:"Serpentine X", 2:"Serpentine Y", 3:f"Diagonal {cfg['angle']}°"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "; ════════════════════════════════════════════════════════════",
        f"; Electrochemistry Scan — {pat_names[cfg['pattern']]}",
        f"; Date/Time    : {now}",
        f"; Plate        : {cfg['plate_w']} × {cfg['plate_h']} mm (centered)",
        f"; Edge offset  : {cfg['edge_offset']} mm (outside plate boundary)",
        f"; Sub-region   : {cfg['sub_w']} × {cfg['sub_h']} mm (centered on plate)",
        f"; Gap          : {cfg['gap']} mm  |  Lines: {cfg['n_lines']}",
        f"; Z-down       : {cfg['z_down']:.1f} mm",
        f"; Speed        : {cfg['speed_mms']:.1f} mm/s  (F{cfg['feedrate']})",
        f"; Skirting     : {SKIRT_PASSES} pass(es), {SKIRT_DWELL_S}s pause",
        "; ════════════════════════════════════════════════════════════",
        "",
        "; Coordinate system: Centered on plate (logical coords)",
        f"; Physical origin (after homeZ12): X={LOGICAL_ORIGIN_X} Y={LOGICAL_ORIGIN_Y} Z={LOGICAL_ORIGIN_Z}",
        "",
        "G21  ; mm units",
        "G90  ; absolute coordinates",
        f"F{cfg['feedrate']}  ; feedrate",
        "",
    ]

def gc_skirt(plate_w, plate_h, edge_offset, z_down):
    """Skirting: 2 consecutive rectangles (outer + inner) with Z movements"""
    
    # First skirting: outer rectangle at full edge_offset
    skirt1_w = plate_w + 2 * edge_offset
    skirt1_h = plate_h + 2 * edge_offset
    x0_skirt1 = f(-skirt1_w / 2)
    x1_skirt1 = f(skirt1_w / 2)
    y0_skirt1 = f(-skirt1_h / 2)
    y1_skirt1 = f(skirt1_h / 2)
    
    # Second skirting: inner rectangle at (edge_offset - 1)
    inner_offset = max(edge_offset - 1, 0.5)  # at least 0.5mm inside
    skirt2_w = plate_w + 2 * inner_offset
    skirt2_h = plate_h + 2 * inner_offset
    x0_skirt2 = f(-skirt2_w / 2)
    x1_skirt2 = f(skirt2_w / 2)
    y0_skirt2 = f(-skirt2_h / 2)
    y1_skirt2 = f(skirt2_h / 2)
    
    lines = [
        "; ════════════════════════════════════════════════════════════",
        "; SKIRTING — 2 consecutive rectangular loops around plate",
        f"; Plate boundary      : ±{plate_w/2:.1f} X, ±{plate_h/2:.1f} Y",
        f"; 1st skirting (outer): ±{skirt1_w/2:.1f} X, ±{skirt1_h/2:.1f} Y  ({edge_offset} mm offset)",
        f"; 2nd skirting (inner): ±{skirt2_w/2:.1f} X, ±{skirt2_h/2:.1f} Y  ({inner_offset} mm offset)",
        f"; Z working depth     : {z_down:.1f} mm",
        f"; Pause before scan   : {SKIRT_DWELL_S} seconds",
        "; ════════════════════════════════════════════════════════════",
        "",
        "; ─── FIRST SKIRTING LOOP (outer, larger rectangle) ───",
        f"G0 X{x0_skirt1} Y{y0_skirt1}  ; move to 1st skirt corner (front-left)",
        f"G0 Z{z_down:.1f}  ; Z down to working depth",
        "; trace 1st rectangle",
        f"G1 X{x1_skirt1} Y{y0_skirt1}  ; → front-right",
        f"G1 X{x1_skirt1} Y{y1_skirt1}  ; → back-right",
        f"G1 X{x0_skirt1} Y{y1_skirt1}  ; → back-left",
        f"G1 X{x0_skirt1} Y{y0_skirt1}  ; → front-left (close loop)",
        f"G0 Z0  ; Z up to safe height",
        "",
        "; ─── SECOND SKIRTING LOOP (inner, smaller rectangle) ───",
        f"G0 X{x0_skirt2} Y{y0_skirt2}  ; move to 2nd skirt corner (front-left)",
        f"G0 Z{z_down:.1f}  ; Z down to working depth",
        "; trace 2nd rectangle",
        f"G1 X{x1_skirt2} Y{y0_skirt2}  ; → front-right",
        f"G1 X{x1_skirt2} Y{y1_skirt2}  ; → back-right",
        f"G1 X{x0_skirt2} Y{y1_skirt2}  ; → back-left",
        f"G1 X{x0_skirt2} Y{y0_skirt2}  ; → front-left (close loop)",
        f"G0 Z0  ; Z up to safe height",
        "",
        "; ─── END SKIRTING, BEFORE SCAN ───",
        f"G4 P{SKIRT_DWELL_S * 1000}  ; PAUSE {SKIRT_DWELL_S} seconds for adjustment",
        "; ────────────────────────────────────────────────────",
    ]
    return lines

def gc_scan_serpentine_x(sub_ox, sub_oy, sub_w, sub_h, gap, n, z_down):
    """Serpentine X: horizontal lines, step in Y"""
    lines = [
        "; ════════════════════════════════════════════════════════════",
        "; SCAN LINES — Serpentine X (horizontal lines stepping in Y)",
        f"; Sub-region: X{sub_ox:.1f}+{sub_w:.1f}, Y{sub_oy:.1f}+{sub_h:.1f}",
        f"; Z depth: {z_down:.1f} mm",
        "; ════════════════════════════════════════════════════════════",
    ]
    
    for i in range(n):
        y = f(sub_oy + i * gap)
        if y > sub_oy + sub_h: break
        xs = f(sub_ox) if i % 2 == 0 else f(sub_ox + sub_w)
        xe = f(sub_ox + sub_w) if i % 2 == 0 else f(sub_ox)
        dir_label = "→" if i % 2 == 0 else "←"
        lines += [
            f"G0 X{xs} Y{y}  ; line {i+1} start {dir_label}",
            f"G1 X{xe} Y{y}  ; line {i+1} scan",
        ]
    return lines

def gc_scan_serpentine_y(sub_ox, sub_oy, sub_w, sub_h, gap, n, z_down):
    """Serpentine Y: vertical lines, step in X"""
    lines = [
        "; ════════════════════════════════════════════════════════════",
        "; SCAN LINES — Serpentine Y (vertical lines stepping in X)",
        f"; Sub-region: X{sub_ox:.1f}+{sub_w:.1f}, Y{sub_oy:.1f}+{sub_h:.1f}",
        f"; Z depth: {z_down:.1f} mm",
        "; ════════════════════════════════════════════════════════════",
    ]
    
    for i in range(n):
        x = f(sub_ox + i * gap)
        if x > sub_ox + sub_w: break
        ys = f(sub_oy) if i % 2 == 0 else f(sub_oy + sub_h)
        ye = f(sub_oy + sub_h) if i % 2 == 0 else f(sub_oy)
        dir_label = "↑" if i % 2 == 0 else "↓"
        lines += [
            f"G0 X{x} Y{ys}  ; line {i+1} start {dir_label}",
            f"G1 X{x} Y{ye}  ; line {i+1} scan",
        ]
    return lines

def gc_scan_diagonal(sub_ox, sub_oy, sub_w, sub_h, gap, n, angle_deg, z_down):
    """Diagonal: lines at angle"""
    lines = [
        "; ════════════════════════════════════════════════════════════",
        f"; SCAN LINES — Diagonal {angle_deg}° (zigzag)",
        f"; Sub-region: X{sub_ox:.1f}+{sub_w:.1f}, Y{sub_oy:.1f}+{sub_h:.1f}",
        f"; Z depth: {z_down:.1f} mm",
        "; ════════════════════════════════════════════════════════════",
    ]
    
    ar = math.radians(angle_deg)
    ca, sa = math.cos(ar), math.sin(ar)
    hl = math.hypot(sub_w, sub_h) * 1.5
    
    for i in range(n):
        mx = sub_ox + sub_w/2 + i * gap * (-sa)
        my = sub_oy + sub_h/2 + i * gap * math.cos(ar)
        p1, p2 = clip_line(mx - hl*ca, my - hl*sa,
                            mx + hl*ca, my + hl*sa,
                            sub_ox, sub_ox + sub_w,
                            sub_oy, sub_oy + sub_h)
        if p1 is None or p2 is None: continue
        x1, y1 = f(p1[0]), f(p1[1])
        x2, y2 = f(p2[0]), f(p2[1])
        if i % 2 == 1: x1, y1, x2, y2 = x2, y2, x1, y1
        lines += [
            f"G0 X{x1} Y{y1}  ; line {i+1} start",
            f"G1 X{x2} Y{y2}  ; line {i+1} scan",
        ]
    return lines

def gc_footer():
    return [
        "",
        "; ────────────────────────────────────────────────────",
        "; END OF SCAN",
        "G0 Z0      ; move Z back to safe height",
        "G0 X0 Y0   ; return to center origin",
        "M84 S0     ; disable motors",
        "",
    ]

def build_gcode(cfg):
    gc = gc_header(cfg)
    gc += gc_skirt(cfg['plate_w'], cfg['plate_h'], cfg['edge_offset'], cfg['z_down'])
    gc.append("")
    
    args = (cfg['sub_ox'], cfg['sub_oy'], cfg['sub_w'], cfg['sub_h'],
            cfg['gap'], cfg['n_lines'], cfg['z_down'])
    p = cfg['pattern']
    if p == 1:   gc += gc_scan_serpentine_x(*args)
    elif p == 2: gc += gc_scan_serpentine_y(*args)
    else:        gc += gc_scan_diagonal(*args, cfg['angle'])
    
    gc += gc_footer()
    return "\n".join(gc)


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    print()
    sep("═")
    print("  GCode Generator — Anycubic Mega X Electrochemistry")
    sep("═")
    
    info_box("Coordinate System", [
        f"Plate-centered coordinates (centered at machine center)",
        f"After homeZ12.gcode: logical (0,0,0) = physical (150,150,120)",
        f"Plate center always at logical X=0, Y=0",
        f"X range: -150 to +150 mm (300mm bed width)",
        f"Y range: -150 to +150 mm (300mm bed height)",
    ])
    
    # ── STEP 1: Plate dimensions ──────────────────────────────────────────
    sep()
    print("\n[ Step 1 of 7 ]  Plate dimensions (centered)")
    print("  Enter plate size. Plate will be centered at machine origin.\n")
    plate_w = prompt_float("  Plate width  (mm): ")
    plate_h = prompt_float("  Plate height (mm): ")
    print(f"  → Plate: {plate_w} × {plate_h} mm")
    print(f"     Plate X range: {-plate_w/2:.1f} to {plate_w/2:.1f} mm")
    print(f"     Plate Y range: {-plate_h/2:.1f} to {plate_h/2:.1f} mm")
    
    # ── STEP 2: Pattern ───────────────────────────────────────────────────
    sep()
    print("\n[ Step 2 of 7 ]  Scan pattern")
    print("  1  Serpentine X  — horizontal lines (← →)")
    print("  2  Serpentine Y  — vertical lines (↑ ↓)")
    print("  3  Diagonal      — angled lines (zigzag)\n")
    pattern = prompt_int("  Choose [1/2/3]: ", choices=[1, 2, 3])
    angle_deg = 45.0
    if pattern == 3:
        angle_deg = prompt_float("  Angle in degrees (0–179): ", allow_zero=True, max_val=179.9)
    pat_names = {1:"Serpentine X", 2:"Serpentine Y", 3:f"Diagonal {angle_deg}°"}
    print(f"  → Pattern: {pat_names[pattern]}")
    
    # ── STEP 3: Edge offset (outside plate boundary for skirting) ─────────
    sep()
    print("\n[ Step 3 of 7 ]  Edge offset for skirting (outside plate)")
    print("  Tool will draw skirting rectangle OUTSIDE the plate boundary.")
    print("  Example: 100×100 plate with 2mm offset → skirting is 104×104\n")
    edge_offset = prompt_float("  Edge offset (0–10 mm): ", allow_zero=True, max_val=10)
    skirt_w = plate_w + 2 * edge_offset
    skirt_h = plate_h + 2 * edge_offset
    print(f"  → Skirting rectangle: {skirt_w} × {skirt_h} mm")
    print(f"     (Plate {plate_w} × {plate_h} + 2×{edge_offset} mm offset)")
    
    # ── STEP 4: Sub-region (width × length only, auto-centered) ──────────
    sep()
    print("\n[ Step 4 of 7 ]  Sub-region (scan area)")
    print(f"  Full plate is {plate_w} × {plate_h} mm.")
    print("  Do you want to scan the entire plate or a smaller sub-region?")
    print("  Sub-region will be centered on the plate (equal margins on all sides).\n")
    scan_full = prompt_yes_no("  Scan entire plate?")
    
    if scan_full:
        sub_w, sub_h = plate_w, plate_h
        sub_ox = -plate_w / 2
        sub_oy = -plate_h / 2
        print(f"  → Full plate: {sub_w} × {sub_h} mm")
    else:
        print(f"\n  Enter sub-region size. It will be centered on the plate.\n")
        sub_w = prompt_float(f"  Sub-region width  (mm, max {plate_w}): ", max_val=plate_w)
        sub_h = prompt_float(f"  Sub-region height (mm, max {plate_h}): ", max_val=plate_h)
        # Center the sub-region
        sub_ox = -sub_w / 2
        sub_oy = -sub_h / 2
        margin_x = (plate_w - sub_w) / 2
        margin_y = (plate_h - sub_h) / 2
        print(f"\n  → Sub-region: {sub_w} × {sub_h} mm (centered)")
        print(f"     Margins: {margin_x:.1f} mm on left/right, {margin_y:.1f} mm on front/back")
        print(f"     X range: {sub_ox:.1f} to {sub_ox+sub_w:.1f} mm")
        print(f"     Y range: {sub_oy:.1f} to {sub_oy+sub_h:.1f} mm")
    
    # ── STEP 5: Gap ───────────────────────────────────────────────────────
    sep()
    print("\n[ Step 5 of 7 ]  Line spacing (gap)")
    print(f"  Distance between parallel scan lines.\n")
    
    while True:
        gap = prompt_float("  Gap (mm): ")
        if not gap_fits(sub_w, sub_h, pattern, gap, angle_deg):
            warn_box("GAP TOO LARGE", [
                f"Gap {gap} mm exceeds available span.",
                "→ Enter a smaller gap.",
            ])
            print(); continue
        break
    
    ml = max_lines_possible(sub_w, sub_h, pattern, gap, angle_deg)
    print()
    info_box(f"Lines that fit: {ml}", [
        f"Scan area     : {sub_w} × {sub_h} mm",
        f"Gap           : {gap} mm",
        f"Step direction: {'Y (height)' if pattern==1 else 'X (width)' if pattern==2 else 'diagonal'}",
        "",
        f"Maximum lines : {ml}",
        "",
        f"Do you want fewer lines, or is {ml} okay?",
    ])
    print()
    
    # ── STEP 5b: Number of lines ──────────────────────────────────────────
    print(f"[ Step 5b of 7 ]  Number of lines")
    while True:
        raw = input(f"  Enter line count [1–{ml}, Enter=all {ml}]: ").strip()
        if raw == "":
            n_lines = ml
            print(f"  → Using all {ml} lines")
            break
        try:
            n_lines = int(raw)
        except ValueError:
            print("  ✗  Enter a whole number."); continue
        
        if n_lines < 1:
            print("  ✗  Must be ≥ 1."); continue
        if n_lines > ml:
            warn_box("TOO MANY LINES", [
                f"You entered    : {n_lines} lines",
                f"Maximum allowed: {ml} lines",
                "",
                f"→ Enter a value ≤ {ml}",
            ])
            print(); continue
        print(f"  → {n_lines} lines")
        break
    
    # ── STEP 6: Z-down depth ──────────────────────────────────────────────
    sep()
    print("\n[ Step 6 of 7 ]  Z-down working depth")
    print(f"  Choose from available depths (0.2 mm increments)\n")
    
    # Generate list: -9.0, -9.2, -9.4, ... -12.8, -13.0 (0.2mm steps)
    available_z = []
    z = Z_DOWN_MAX
    while z >= Z_DOWN_HARD_LIMIT - 0.01:  # small tolerance for float comparison
        available_z.append(round(z, 1))
        z = round(z - 0.2, 1)
    
    # Display in a grid format
    info_box("Available Z-down depths (0.2 mm steps)", [
        f"Shallowest (safest)  : {Z_DOWN_MAX:.1f} mm",
        f"Recommended range    : -10.0 to -11.0 mm",
        f"Deepest (hard limit) : {Z_DOWN_HARD_LIMIT:.1f} mm (tool touches surface)",
        "",
        f"Total options: {len(available_z)} depths available",
    ])
    print()
    
    # Show all available values in columns (4 per row)
    print("  Available Z values:")
    cols = 4
    for i in range(0, len(available_z), cols):
        row = available_z[i:i+cols]
        print("    " + "  ".join(f"{z:.1f}mm" for z in row))
    print()
    
    # Ask user to choose
    while True:
        raw = input("  Choose a Z-down depth (e.g., -11.0): ").strip()
        try:
            z_down = float(raw)
            z_down = round(z_down, 1)
        except ValueError:
            print("  ✗  Enter a valid number."); continue
        
        # Check if it's in the available list
        if z_down not in available_z:
            warn_box("Z VALUE NOT IN AVAILABLE LIST", [
                f"You entered  : {z_down:.1f} mm",
                f"",
                f"Available Z uses 0.2 mm increments:",
                f"-9.0, -9.2, -9.4, -9.6, -9.8, -10.0, ..., -12.8, -13.0",
                "",
                f"→ Choose from the list above",
            ])
            print(); continue
        
        break
    
    print(f"  → Z working depth: {z_down:.1f} mm")
    
    # ── STEP 7: Speed ─────────────────────────────────────────────────────
    sep()
    print(f"\n[ Step 7 of 7 ]  Tool travel speed")
    print("  Enter feedrate (mm/min).")
    print("  Program will show equivalent mm/s + safety info.\n")
    
    info_box("Speed reference (Anycubic Mega X)", [
        f"Minimum (safest)     : 20 mm/s   (1200 mm/min)  — very slow",
        f"Recommended (good)   : 40–60 mm/s  (2400–3600 mm/min)  — balanced",
        f"Fast (risky)         : 80–100 mm/s  (4800–6000 mm/min)  — maximum speed",
        f"",
        f"Hard limit (must not exceed): 100 mm/s (6000 mm/min)",
    ])
    print()
    
    speed_mms = 0.0
    feedrate = 0.0
    speed_confirmed = False
    while not speed_confirmed:
        while True:
            feedrate = prompt_float("  Feedrate (F value, mm/min): ")
            speed_mms = feedrate / 60.0
            feedrate = speed_mms * 60.0  # 
            if speed_mms > MEGA_X_MAX_MMS:
                warn_box("SPEED EXCEEDS MACHINE LIMIT", [
                    f"You entered: {feedrate:.0f} mm/min = {speed_mms:.1f} mm/s",
                    f"Machine max: {MEGA_X_MAX_MMS} mm/s  (hard limit)",
                    "",
                    f"→ Enter a feedrate ≤ {MEGA_X_MAX_MMS * 60:.0f} mm/min",
                ])
                print(); continue
            break
        
        print(f"\n  → Feedrate: {feedrate:.0f} mm/min = {speed_mms:.1f} mm/s")
        
        # Show safety classification
        if speed_mms <= 20:
            classification = "🟢 VERY SAFE (slow)"
        elif speed_mms <= 40:
            classification = "🟢 SAFE (slow to moderate)"
        elif speed_mms <= 60:
            classification = "🟢 RECOMMENDED (good balance)"
        elif speed_mms <= 80:
            classification = "🟡 FAST (monitor carefully)"
        else:
            classification = "🔴 VERY FAST (risky, near limit)"
        
        print(f"  {classification}\n")
        
        if prompt_yes_no("  Keep this speed?"):
            speed_confirmed = True
        else:
            print("\n  Enter a different feedrate:\n")
    
    # ── BUILD ─────────────────────────────────────────────────────────────
    cfg = {
        "plate_w": plate_w, "plate_h": plate_h,
        "pattern": pattern, "angle": angle_deg,
        "edge_offset": edge_offset,
        "sub_ox": sub_ox, "sub_oy": sub_oy,
        "sub_w": sub_w, "sub_h": sub_h,
        "gap": gap, "n_lines": n_lines,
        "z_down": z_down,
        "speed_mms": speed_mms, "feedrate": feedrate,
    }
    
    sep("═")
    print("\n  FINAL SUMMARY")
    print()
    ok_box("Scan sequence", [
        f"1. Tool moves to skirt corner",
        f"2. Pauses {SKIRT_DWELL_S} seconds (for adjustment)",
        f"3. Z down to {z_down:.1f} mm (working depth)",
        f"4. Draws 1 skirting rectangle around plate",
        f"5. Scans {n_lines} {pat_names[pattern]} lines",
        f"   Region: {sub_w} × {sub_h} mm (centered on {plate_w}×{plate_h} plate)",
        f"   Gap: {gap} mm",
        f"   Speed: {speed_mms:.1f} mm/s  (F{feedrate:.0f})",
        f"6. Z up to 0 mm (safe height)",
        f"7. Returns to center origin",
    ])
    print()
    
    gcode_text = build_gcode(cfg)
    all_lines = gcode_text.split("\n")
    move_cnt = sum(1 for l in all_lines if l.startswith(("G0", "G1")))
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = pat_names[pattern].replace(" ", "_").replace("(", "").replace(")", "").replace("°", "deg")
    out = OUTPUT_FOLDER / f"scan_{slug}_{ts}.gcode"
    out.write_text(gcode_text, encoding="utf-8")
    
    sep("═")
    print(f"  ✓  Generated {move_cnt} motion commands")
    print(f"  ✓  Saved to: {out.resolve()}")
    sep("═")
    
    print("\n  ── GCode preview (first 14 lines) ──\n")
    for line in all_lines[:20]:
        if line.strip() and not line.startswith(";"):
            print(f"  {line}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Aborted."); sys.exit(0)
