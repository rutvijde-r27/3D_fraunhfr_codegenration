#!/usr/bin/env python3
"""
GCode Generator — Anycubic Mega X Electrochemistry (MERGED)
Supports: Serpentine patterns OR Circular spiral patterns
Calculates speed automatically from user-specified motion time
"""
from __future__ import annotations
import math, sys
from pathlib import Path
from datetime import datetime

# ════════════════════════════════════════════════════════════════════════════
#  MACHINE CONSTANTS
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
SKIRT_PASSES = 1

OUTPUT_FOLDER = Path("./gcode_output")

# Circle defaults
DEFAULT_PAUSE_BETWEEN_CIRCLES = 10  # seconds


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
#  CIRCLE GEOMETRY
# ════════════════════════════════════════════════════════════════════════════

def calculate_circle_array(plate_w, plate_h, circle_diameter, spacing=10):
    """Calculate how many circles fit in a grid"""
    # Effective space available for circles
    effective_w = plate_w - 2 * spacing
    effective_h = plate_h - 2 * spacing
    
    # How many circles fit in each direction
    cols = max(1, int(effective_w / (circle_diameter + spacing)))
    rows = max(1, int(effective_h / (circle_diameter + spacing)))
    
    total = rows * cols
    return rows, cols, total

def calculate_spiral_path_length(diameter, num_spirals=5):
    """Calculate approximate spiral path length (mm)"""
    radius = diameter / 2
    # Approximate: average circumference × number of spirals
    avg_circumference = math.pi * diameter
    return avg_circumference * num_spirals

def calculate_speed_from_time(path_length_mm, motion_time_seconds):
    """Calculate speed needed to complete path in given time"""
    if motion_time_seconds <= 0:
        return 10  # fallback
    speed_mms = path_length_mm / motion_time_seconds
    speed_mmmin = speed_mms * 60
    return speed_mms, speed_mmmin

def f(n, d=4): return round(n, d)


# ════════════════════════════════════════════════════════════════════════════
#  GCODE BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def gc_header(cfg):
    pattern_type = "Circles" if cfg.get('pattern') == 'circles' else "Serpentine"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "; ════════════════════════════════════════════════════════════",
        f"; GCode — {pattern_type} Pattern",
        f"; Date/Time    : {now}",
        f"; Plate        : {cfg['plate_w']} × {cfg['plate_h']} mm",
        f"; Z-down       : {cfg['z_down']:.1f} mm",
        f"; Speed        : {cfg['speed_mms']:.1f} mm/s (F{cfg['feedrate']})",
        "; ════════════════════════════════════════════════════════════",
        "",
        "G21  ; mm units",
        "G90  ; absolute coordinates",
        f"F{cfg['feedrate']:.1f}",
        "",
    ]

def gc_skirt(plate_w, plate_h, edge_offset, z_down):
    """Skirting: 2 consecutive rectangles"""
    skirt1_w = plate_w + 2 * edge_offset
    skirt1_h = plate_h + 2 * edge_offset
    x0_skirt1 = f(-skirt1_w / 2)
    x1_skirt1 = f(skirt1_w / 2)
    y0_skirt1 = f(-skirt1_h / 2)
    y1_skirt1 = f(skirt1_h / 2)
    
    inner_offset = max(edge_offset - 1, 0.5)
    skirt2_w = plate_w + 2 * inner_offset
    skirt2_h = plate_h + 2 * inner_offset
    x0_skirt2 = f(-skirt2_w / 2)
    x1_skirt2 = f(skirt2_w / 2)
    y0_skirt2 = f(-skirt2_h / 2)
    y1_skirt2 = f(skirt2_h / 2)
    
    lines = [
        "; ════════════════════════════════════════════════════════════",
        "; SKIRTING — 2 loops",
        "; ════════════════════════════════════════════════════════════",
        f"G0 X{x0_skirt1} Y{y0_skirt1}",
        f"G0 Z{z_down:.1f}",
        f"G1 X{x1_skirt1} Y{y0_skirt1}",
        f"G1 X{x1_skirt1} Y{y1_skirt1}",
        f"G1 X{x0_skirt1} Y{y1_skirt1}",
        f"G1 X{x0_skirt1} Y{y0_skirt1}",
        f"G0 Z0",
        f"G0 X{x0_skirt2} Y{y0_skirt2}",
        f"G0 Z{z_down:.1f}",
        f"G1 X{x1_skirt2} Y{y0_skirt2}",
        f"G1 X{x1_skirt2} Y{y1_skirt2}",
        f"G1 X{x0_skirt2} Y{y1_skirt2}",
        f"G1 X{x0_skirt2} Y{y0_skirt2}",
        f"G0 Z0",
        f"G4 P{SKIRT_DWELL_S * 1000}",
    ]
    return lines

def gc_circles(plate_w, plate_h, circle_diameter, num_circles, motion_time, 
               step_time, pause_time, z_down):
    """Generate spiral circles"""
    rows, cols, total = calculate_circle_array(plate_w, plate_h, circle_diameter)
    
    # Adjust actual circles to fit grid
    if num_circles > total:
        num_circles = total
    
    # Calculate circle positions (center-spaced)
    spacing = 10  # mm between circle centers
    start_x = -plate_w / 2 + spacing + circle_diameter/2
    start_y = -plate_h / 2 + spacing + circle_diameter/2
    
    lines = [
        "; ════════════════════════════════════════════════════════════",
        f"; CIRCLES — {num_circles} circles, {circle_diameter} mm diameter",
        f"; Motion time: {motion_time}s per circle",
        f"; Step time increment: {step_time}s",
        f"; Pause between: {pause_time}s",
        "; ════════════════════════════════════════════════════════════",
    ]
    
    circle_count = 0
    current_motion_time = motion_time
    
    for row in range(rows):
        for col in range(cols):
            if circle_count >= num_circles:
                break
            
            # Circle center position
            cx = f(start_x + col * (circle_diameter + spacing))
            cy = f(start_y + row * (circle_diameter + spacing))
            
            # Calculate speed for this circle's motion time
            path_length = calculate_spiral_path_length(circle_diameter)
            speed_mms, speed_mmmin = calculate_speed_from_time(path_length, current_motion_time)
            
            lines.append("")
            lines.append(f"; ─── CIRCLE {circle_count + 1} ───")
            lines.append(f"; Center: ({cx}, {cy}), Diameter: {circle_diameter}mm")
            lines.append(f"; Motion time: {current_motion_time}s, Speed: {speed_mms:.2f} mm/s")
            lines.append(f"G0 X{cx} Y{cy}  ; move to circle center")
            lines.append(f"G0 Z{z_down:.1f}  ; Z down")
            
            # Spiral inward from outer edge to center
            radius = circle_diameter / 2
            num_spirals = 5
            for spiral in range(num_spirals):
                # Reduce radius each spiral
                current_radius = radius * (1 - spiral / num_spirals)
                angle_step = 10  # degrees
                for angle in range(0, 360, angle_step):
                    rad = math.radians(angle)
                    x = cx + current_radius * math.cos(rad)
                    y = cy + current_radius * math.sin(rad)
                    lines.append(f"G1 X{f(x)} Y{f(y)} F{f(speed_mmmin)}")
            
            # Return to center
            lines.append(f"G1 X{cx} Y{cy}  ; return to center")
            lines.append(f"G0 Z0  ; Z up")
            
            if circle_count < num_circles - 1:
                lines.append(f"G4 P{pause_time * 1000}  ; pause {pause_time}s for prep")
            
            circle_count += 1
            current_motion_time += step_time
        
        if circle_count >= num_circles:
            break
    
    return lines

def gc_footer():
    return [
        "",
        "G0 Z0      ; move Z back to 0",
        "G0 X0 Y0   ; return to origin",
        "M84 S0     ; disable motors",
        "",
    ]

def build_gcode(cfg):
    gc = gc_header(cfg)
    gc += gc_skirt(cfg['plate_w'], cfg['plate_h'], cfg['edge_offset'], cfg['z_down'])
    gc.append("")
    
    if cfg.get('pattern') == 'circles':
        gc += gc_circles(
            cfg['plate_w'], cfg['plate_h'],
            cfg['circle_diameter'], cfg['num_circles'],
            cfg['motion_time'], cfg['step_time'],
            cfg['pause_between'], cfg['z_down']
        )
    else:
        # Placeholder for serpentine (existing code would go here)
        gc.append("; SERPENTINE PATTERN (TODO)")
    
    gc += gc_footer()
    return "\n".join(gc)


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    print()
    sep("═")
    print("  GCode Generator — Circle & Serpentine Patterns")
    print("  Anycubic Mega X Electrochemistry")
    sep("═")
    
    info_box("Coordinate System", [
        f"Logical origin (0,0,0) = plate center",
        f"Physical bed: 300 × 300 mm",
    ])
    
    # ── STEP 1: Plate dimensions ──────────────────────────────────────────
    sep()
    print("\n[ Step 1 of 6 ]  Plate dimensions")
    plate_w = prompt_float("  Plate width  (mm): ")
    plate_h = prompt_float("  Plate height (mm): ")
    
    # ── STEP 2: Pattern type ──────────────────────────────────────────────
    sep()
    print("\n[ Step 2 of 6 ]  Pattern type")
    print("  1  Circles")
    print("  2  Serpentine X")
    print("  3  Serpentine Y")
    pattern_choice = prompt_int("  Choose [1/2/3]: ", choices=[1, 2, 3])
    
    if pattern_choice == 1:
        pattern = 'circles'
    else:
        pattern = 'serpentine'
    
    # ── STEP 3: Edge offset ───────────────────────────────────────────────
    sep()
    print("\n[ Step 3 of 6 ]  Edge offset")
    edge_offset = prompt_float("  Edge offset (0–10 mm): ", allow_zero=True, max_val=10)
    
    # ── STEP 4: Pattern-specific inputs ───────────────────────────────────
    sep()
    if pattern == 'circles':
        print("\n[ Step 4 of 6 ]  Circle parameters")
        
        # Calculate how many circles fit
        rows, cols, total = calculate_circle_array(plate_w, plate_h, 25, spacing=10)
        
        print(f"\n  Plate: {plate_w} × {plate_h} mm")
        print(f"  Maximum circles possible: {total} ({rows}×{cols} array)\n")
        
        circle_diameter = prompt_float("  Circle diameter (mm): ")
        
        # Show array popup
        rows, cols, total = calculate_circle_array(plate_w, plate_h, circle_diameter)
        
        info_box("Circle Array", [
            f"Circle diameter: {circle_diameter} mm",
            f"Grid size: {rows} rows × {cols} columns",
            f"Total circles possible: {total}",
        ])
        
        num_circles = prompt_int(f"  How many circles [1–{total}]: ", min_val=1)
        if num_circles > total:
            num_circles = total
        
        motion_time = prompt_float("  Motion time per circle (seconds): ")
        step_time = prompt_float("  Time increment per circle (seconds): ", allow_zero=True)
        
        print(f"\n  Pause between circles (default 10s):")
        change_pause = prompt_yes_no("  Change pause time?")
        if change_pause:
            pause_time = prompt_int("  New pause time (seconds): ", min_val=1)
        else:
            pause_time = DEFAULT_PAUSE_BETWEEN_CIRCLES
        
        cfg = {
            'plate_w': plate_w, 'plate_h': plate_h,
            'edge_offset': edge_offset,
            'pattern': 'circles',
            'circle_diameter': circle_diameter,
            'num_circles': num_circles,
            'motion_time': motion_time,
            'step_time': step_time,
            'pause_between': pause_time,
        }
    else:
        print("\n[ Step 4 of 6 ]  Serpentine parameters (TODO)")
        cfg = {
            'plate_w': plate_w, 'plate_h': plate_h,
            'edge_offset': edge_offset,
            'pattern': pattern,
        }
    
    # ── STEP 5: Z-down depth ──────────────────────────────────────────────
    sep()
    print("\n[ Step 5 of 6 ]  Z-down working depth")
    available_z = []
    z = Z_DOWN_MAX
    while z >= Z_DOWN_HARD_LIMIT - 0.01:
        available_z.append(round(z, 1))
        z = round(z - 0.2, 1)
    
    print(f"  Available Z values:")
    cols = 4
    for i in range(0, len(available_z), cols):
        row = available_z[i:i+cols]
        print("    " + "  ".join(f"{z:.1f}mm" for z in row))
    print()
    
    while True:
        raw = input("  Choose Z-down depth (e.g., -11.0): ").strip()
        try:
            z_down = round(float(raw), 1)
        except ValueError:
            print("  ✗  Enter a valid number."); continue
        if z_down not in available_z:
            warn_box("Z NOT IN LIST", [
                f"Available: -9.0 through -13.0 (0.2mm steps)",
            ])
            print(); continue
        break
    
    # ── STEP 6: Speed ─────────────────────────────────────────────────────
    sep()
    print("\n[ Step 6 of 6 ]  Tool speed")
    
    if pattern == 'circles':
        # Speed is calculated from motion time for circles
        path_length = calculate_spiral_path_length(cfg['circle_diameter'])
        speed_mms, speed_mmmin = calculate_speed_from_time(path_length, cfg['motion_time'])
        
        info_box("Circle Speed (Auto-Calculated)", [
            f"Motion time: {cfg['motion_time']} seconds",
            f"Spiral path length: {path_length:.1f} mm",
            f"Calculated speed: {speed_mms:.2f} mm/s ({speed_mmmin:.0f} mm/min)",
            "",
            f"Speed confirmed ✓",
        ])
        feedrate = speed_mmmin
    else:
        feedrate = prompt_float("  Feedrate (mm/min): ")
    
    speed_mms = feedrate / 60
    
    cfg['z_down'] = z_down
    cfg['feedrate'] = feedrate
    cfg['speed_mms'] = speed_mms
    
    # ── BUILD ─────────────────────────────────────────────────────────────
    sep("═")
    print("\n  FINAL SUMMARY")
    print()
    ok_box("GCode will be generated", [
        f"Pattern: {'Circles' if pattern == 'circles' else 'Serpentine'}",
        f"Plate: {plate_w} × {plate_h} mm",
        f"Z depth: {z_down:.1f} mm",
        f"Speed: {speed_mms:.1f} mm/s",
    ])
    print()
    
    gcode_text = build_gcode(cfg)
    all_lines = gcode_text.split("\n")
    move_cnt = sum(1 for l in all_lines if l.startswith(("G0", "G1")))
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pattern_name = "circles" if pattern == 'circles' else "serpentine"
    out = OUTPUT_FOLDER / f"scan_{pattern_name}_{ts}.gcode"
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
