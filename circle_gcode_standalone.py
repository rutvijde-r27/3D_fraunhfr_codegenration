#!/usr/bin/env python3
"""
GCode Generator — Circle Spiral Patterns ONLY
Standalone version for electrochemistry circular motion
Auto-calculates speed from user-specified motion time
"""
from __future__ import annotations
import math, sys
from pathlib import Path
from datetime import datetime

# ════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ════════════════════════════════════════════════════════════════════════════

LOGICAL_ORIGIN_X = 150
LOGICAL_ORIGIN_Y = 150
LOGICAL_ORIGIN_Z = 120

MEGA_X_BUILD_X = 300
MEGA_X_BUILD_Y = 300
MEGA_X_MAX_MMS = 100

Z_DOWN_MAX = -9.0
Z_DOWN_HARD_LIMIT = -13.0

SKIRT_DWELL_S = 90

OUTPUT_FOLDER = Path("./gcode_output")

DEFAULT_PAUSE_BETWEEN_CIRCLES = 10


# ════════════════════════════════════════════════════════════════════════════
#  VISUAL
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
#  INPUT
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
#  CIRCLE MATH
# ════════════════════════════════════════════════════════════════════════════

def calculate_circle_array(plate_w, plate_h, circle_diameter, spacing=10):
    """Calculate circle grid"""
    effective_w = plate_w - 2 * spacing
    effective_h = plate_h - 2 * spacing
    
    cols = max(1, int(effective_w / (circle_diameter + spacing)))
    rows = max(1, int(effective_h / (circle_diameter + spacing)))
    
    return rows, cols, rows * cols

def calculate_spiral_path_length(diameter, num_spirals=5):
    """Spiral path length"""
    radius = diameter / 2
    avg_circumference = math.pi * diameter
    return avg_circumference * num_spirals

def calculate_speed_from_time(path_length_mm, motion_time_seconds):
    """Speed from motion time"""
    if motion_time_seconds <= 0:
        return 10.0, 600.0
    speed_mms = path_length_mm / motion_time_seconds
    speed_mmmin = speed_mms * 60
    return speed_mms, speed_mmmin

def f(n, d=4): return round(n, d)


# ════════════════════════════════════════════════════════════════════════════
#  GCODE
# ════════════════════════════════════════════════════════════════════════════

def gc_header(cfg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "; ════════════════════════════════════════════════════════════",
        f"; Circle Spiral Pattern",
        f"; Date/Time    : {now}",
        f"; Plate        : {cfg['plate_w']} × {cfg['plate_h']} mm",
        f"; Circles      : {cfg['num_circles']} circles, {cfg['circle_diameter']} mm diameter",
        f"; Motion time  : {cfg['motion_time']} sec per circle",
        f"; Z-down       : {cfg['z_down']:.1f} mm",
        "; ════════════════════════════════════════════════════════════",
        "",
        "G21  ; mm units",
        "G90  ; absolute coordinates",
        "",
    ]

def gc_skirt(plate_w, plate_h, edge_offset, z_down):
    """Skirting"""
    skirt1_w = plate_w + 2 * edge_offset
    skirt1_h = plate_h + 2 * edge_offset
    x0_s1 = f(-skirt1_w / 2)
    x1_s1 = f(skirt1_w / 2)
    y0_s1 = f(-skirt1_h / 2)
    y1_s1 = f(skirt1_h / 2)
    
    inner_offset = max(edge_offset - 1, 0.5)
    skirt2_w = plate_w + 2 * inner_offset
    skirt2_h = plate_h + 2 * inner_offset
    x0_s2 = f(-skirt2_w / 2)
    x1_s2 = f(skirt2_w / 2)
    y0_s2 = f(-skirt2_h / 2)
    y1_s2 = f(skirt2_h / 2)
    
    return [
        "; SKIRTING",
        f"G0 X{x0_s1} Y{y0_s1}",
        f"G0 Z{z_down:.1f}",
        f"G1 X{x1_s1} Y{y0_s1}",
        f"G1 X{x1_s1} Y{y1_s1}",
        f"G1 X{x0_s1} Y{y1_s1}",
        f"G1 X{x0_s1} Y{y0_s1}",
        f"G0 Z0",
        f"G0 X{x0_s2} Y{y0_s2}",
        f"G0 Z{z_down:.1f}",
        f"G1 X{x1_s2} Y{y0_s2}",
        f"G1 X{x1_s2} Y{y1_s2}",
        f"G1 X{x0_s2} Y{y1_s2}",
        f"G1 X{x0_s2} Y{y0_s2}",
        f"G0 Z0",
        f"G4 P{SKIRT_DWELL_S * 1000}",
        "",
    ]

def gc_circles(cfg):
    """Generate circles"""
    plate_w = cfg['plate_w']
    plate_h = cfg['plate_h']
    circle_diameter = cfg['circle_diameter']
    num_circles = cfg['num_circles']
    motion_time = cfg['motion_time']
    step_time = cfg['step_time']
    pause_time = cfg['pause_between']
    z_down = cfg['z_down']
    
    rows, cols, total = calculate_circle_array(plate_w, plate_h, circle_diameter)
    
    # Positions
    spacing = 10
    start_x = -plate_w / 2 + spacing + circle_diameter/2
    start_y = -plate_h / 2 + spacing + circle_diameter/2
    
    lines = [
        "; ════════════════════════════════════════════════════════════",
        f"; CIRCLE SPIRALS — {num_circles} circles",
        f"; Motion time: {motion_time}s, Step: {step_time}s, Pause: {pause_time}s",
        "; ════════════════════════════════════════════════════════════",
        "",
    ]
    
    circle_count = 0
    current_motion_time = motion_time
    
    for row in range(rows):
        for col in range(cols):
            if circle_count >= num_circles:
                break
            
            cx = f(start_x + col * (circle_diameter + spacing))
            cy = f(start_y + row * (circle_diameter + spacing))
            
            path_length = calculate_spiral_path_length(circle_diameter)
            speed_mms, speed_mmmin = calculate_speed_from_time(path_length, current_motion_time)
            
            lines.append(f"; ─── CIRCLE {circle_count + 1} ───")
            lines.append(f"; Center: ({cx}, {cy}), Time: {current_motion_time}s, Speed: {speed_mms:.2f}mm/s")
            lines.append(f"G0 X{cx} Y{cy}")
            lines.append(f"G0 Z{z_down:.1f}")
            
            # Spiral
            radius = circle_diameter / 2
            num_spirals = 5
            for spiral in range(num_spirals):
                current_radius = radius * (1 - spiral / num_spirals)
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    x = cx + current_radius * math.cos(rad)
                    y = cy + current_radius * math.sin(rad)
                    lines.append(f"G1 X{f(x)} Y{f(y)} F{f(speed_mmmin)}")
            
            lines.append(f"G1 X{cx} Y{cy}")
            lines.append(f"G0 Z0")
            
            if circle_count < num_circles - 1:
                lines.append(f"G4 P{pause_time * 1000}")
            
            lines.append("")
            circle_count += 1
            current_motion_time += step_time
        
        if circle_count >= num_circles:
            break
    
    return lines

def gc_footer():
    return [
        "G0 Z0      ; Z up",
        "G0 X0 Y0   ; origin",
        "M84 S0     ; disable motors",
        "",
    ]

def build_gcode(cfg):
    gc = gc_header(cfg)
    gc += gc_skirt(cfg['plate_w'], cfg['plate_h'], cfg['edge_offset'], cfg['z_down'])
    gc += gc_circles(cfg)
    gc += gc_footer()
    return "\n".join(gc)


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    print()
    sep("═")
    print("  GCode Generator — Circle Spiral Patterns")
    print("  Anycubic Mega X Electrochemistry")
    sep("═")
    
    # STEP 1
    sep()
    print("\n[ Step 1 of 5 ]  Plate dimensions")
    plate_w = prompt_float("  Plate width  (mm): ")
    plate_h = prompt_float("  Plate height (mm): ")
    
    # STEP 2
    sep()
    print("\n[ Step 2 of 5 ]  Edge offset")
    edge_offset = prompt_float("  Edge offset (0–10 mm): ", allow_zero=True, max_val=10)
    
    # STEP 3
    sep()
    print("\n[ Step 3 of 5 ]  Circle parameters")
    
    print(f"  Plate: {plate_w} × {plate_h} mm\n")
    circle_diameter = prompt_float("  Circle diameter (mm): ")
    
    rows, cols, total = calculate_circle_array(plate_w, plate_h, circle_diameter)
    
    # ARRAY POPUP
    info_box("Circle Array Calculation", [
        f"Circle diameter: {circle_diameter} mm",
        f"Grid size: {rows} rows × {cols} columns",
        f"Total circles possible: {total}",
        "",
        "Press Enter to continue...",
    ])
    input()
    
    num_circles = prompt_int(f"  How many circles [1–{total}]: ", min_val=1)
    if num_circles > total:
        print(f"  ⚠ Limited to {total} circles (adjusted)")
        num_circles = total
    
    motion_time = prompt_float("  Motion time per circle (seconds): ")
    step_time = prompt_float("  Time increment per circle (seconds): ", allow_zero=True)
    
    # Pause
    print(f"\n  Pause between circles (default {DEFAULT_PAUSE_BETWEEN_CIRCLES}s):")
    change_pause = prompt_yes_no("  Change pause time?")
    if change_pause:
        pause_time = prompt_int("  New pause time (seconds): ", min_val=1)
    else:
        pause_time = DEFAULT_PAUSE_BETWEEN_CIRCLES
    
    # STEP 4
    sep()
    print("\n[ Step 4 of 5 ]  Z-down working depth")
    
    available_z = []
    z = Z_DOWN_MAX
    while z >= Z_DOWN_HARD_LIMIT - 0.01:
        available_z.append(round(z, 1))
        z = round(z - 0.2, 1)
    
    print(f"  Available Z values:")
    cols_display = 4
    for i in range(0, len(available_z), cols_display):
        row = available_z[i:i+cols_display]
        print("    " + "  ".join(f"{z:.1f}mm" for z in row))
    print()
    
    while True:
        raw = input("  Choose Z-down depth (e.g., -11.0): ").strip()
        try:
            z_down = round(float(raw), 1)
        except ValueError:
            print("  ✗  Enter valid number."); continue
        if z_down not in available_z:
            warn_box("Z NOT IN LIST", ["Available: -9.0 to -13.0 (0.2mm steps)"])
            print(); continue
        break
    
    # STEP 5
    sep()
    print("\n[ Step 5 of 5 ]  Speed (Auto-Calculated)")
    
    path_length = calculate_spiral_path_length(circle_diameter)
    speed_mms, speed_mmmin = calculate_speed_from_time(path_length, motion_time)
    
    info_box("Circle Speed Calculation", [
        f"Spiral path length: {path_length:.1f} mm",
        f"Motion time: {motion_time} seconds",
        f"Calculated speed: {speed_mms:.2f} mm/s ({speed_mmmin:.0f} mm/min)",
        "",
        "✓ Speed auto-calculated and confirmed",
    ])
    
    # BUILD
    cfg = {
        'plate_w': plate_w, 'plate_h': plate_h,
        'edge_offset': edge_offset,
        'circle_diameter': circle_diameter,
        'num_circles': num_circles,
        'motion_time': motion_time,
        'step_time': step_time,
        'pause_between': pause_time,
        'z_down': z_down,
        'speed_mms': speed_mms,
    }
    
    sep("═")
    print("\n  SUMMARY")
    ok_box("Circle Spiral GCode", [
        f"Circles: {num_circles} (diameter {circle_diameter}mm)",
        f"Array: {rows}×{cols}",
        f"Motion time: {motion_time}s (step +{step_time}s)",
        f"Pause: {pause_time}s between circles",
        f"Speed: {speed_mms:.2f}mm/s (auto-calculated)",
        f"Z depth: {z_down:.1f}mm",
    ])
    print()
    
    gcode_text = build_gcode(cfg)
    all_lines = gcode_text.split("\n")
    move_cnt = sum(1 for l in all_lines if l.startswith(("G0", "G1")))
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_FOLDER / f"circles_{ts}.gcode"
    out.write_text(gcode_text, encoding="utf-8")
    
    sep("═")
    print(f"  ✓  {move_cnt} motion commands")
    print(f"  ✓  Saved to: {out.resolve()}")
    sep("═")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Aborted."); sys.exit(0)
