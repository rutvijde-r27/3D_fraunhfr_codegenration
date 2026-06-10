#!/usr/bin/env python3
"""
GCode Generator — Anycubic Mega X Electrochemistry (SERPENTINE INTEGRATED)
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

# Anycubic Mega X specifications (Optimized for slow electrochemical work)
ANYCUBIC_MIN_SPEED = 1    # mm/s (Lower floor for ultra-slow micro-stepping)
ANYCUBIC_MAX_SPEED = 200  # mm/s (Hard ceiling — raised to 200 mm/s)
ANYCUBIC_RECOMMENDED_SPEED = 20  # mm/s

# Job duration limits
DEFAULT_MAX_JOB_DURATION_HOURS = 12

Z_DOWN_MAX = -11.0   # user-selectable start depth
Z_DOWN_HARD_LIMIT = -13.0   # hard floor

SKIRT_DWELL_S = 90
SKIRT_PASSES = 1

# Automatically targets the exact directory where this script file is saved
OUTPUT_FOLDER: Path = Path(__file__).parent.resolve() / "GCode_Generated_Output"

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

def prompt_float(msg, *, allow_zero=False, min_val=0.0, max_val=None, default=None):
    while True:
        user_input = input(msg).strip().replace(",", ".")
        if user_input == "" and default is not None:
            return default
        try:
            v = float(user_input)
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
#  GEOMETRY & MATH CALCULATIONS
# ════════════════════════════════════════════════════════════════════════════

def calculate_circle_array(plate_w, plate_h, circle_diameter, edge_offset, circle_gap):
    effective_w = plate_w - (2 * edge_offset)
    effective_h = plate_h - (2 * edge_offset)
    cols = max(1, int((effective_w + circle_gap) / (circle_diameter + circle_gap)))
    rows = max(1, int((effective_h + circle_gap) / (circle_diameter + circle_gap)))
    return rows, cols, rows * cols

def calculate_spiral_path_length(diameter, num_spirals=5):
    avg_circumference = math.pi * (diameter / 2)
    return avg_circumference * num_spirals

def calculate_serpentine_path_length(w, h, step_over, mode):
    """Calculate the total linear distance of a serpentine grid path"""
    if mode == 'serpentine_x':
        passes = max(1, int(h / step_over) + 1)
        sweep_distance = passes * w
        transition_distance = (passes - 1) * step_over
    else:
        passes = max(1, int(w / step_over) + 1)
        sweep_distance = passes * h
        transition_distance = (passes - 1) * step_over
    return sweep_distance + transition_distance

def calculate_speed_from_time(path_length_mm, motion_time_seconds):
    if motion_time_seconds <= 0:
        return 10, 600
    speed_mms = path_length_mm / motion_time_seconds
    speed_mmmin = speed_mms * 60
    return speed_mms, speed_mmmin

def validate_motion_time(motion_time, path_length):
    speed_mms, _ = calculate_speed_from_time(path_length, motion_time)
    if speed_mms < ANYCUBIC_MIN_SPEED:
        return False, speed_mms, f"Motion time too long! Speed drops below hardware floor of {ANYCUBIC_MIN_SPEED} mm/s"
    if speed_mms > ANYCUBIC_MAX_SPEED:
        return False, speed_mms, f"Motion time too short! Speed exceeds hardware ceiling of {ANYCUBIC_MAX_SPEED} mm/s"
    return True, speed_mms, None

def calculate_total_job_time(base_motion_s, num_elements=1, step_increment_s=0, pause_between_s=0, skirting_s=60):
    total_motion = 0
    for i in range(num_elements):
        total_motion += base_motion_s + (step_increment_s * i)
    total_pauses = max(0, num_elements - 1) * pause_between_s
    total_travel = num_elements * 2
    
    total_s = skirting_s + total_motion + total_pauses + total_travel
    return {
        'seconds': int(total_s),
        'minutes': round(total_s / 60, 1),
        'hours': round(total_s / 3600, 2)
    }

def f(n, d=4): return round(n, d)


# ════════════════════════════════════════════════════════════════════════════
#  GCODE BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def gc_header(cfg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "; ════════════════════════════════════════════════════════════",
        f"; GCode — {cfg['pattern'].upper()} Pattern",
        f"; Date/Time    : {now}",
        f"; Plate        : {cfg['plate_w']} × {cfg['plate_h']} mm",
        f"; Z-down       : {cfg['z_down']:.1f} mm",
        f"; Base Speed   : {cfg['speed_mms']:.1f} mm/s (F{cfg['feedrate']:.1f})",
        "; ════════════════════════════════════════════════════════════",
        "",
        "G21  ; metric standard",
        "G90  ; absolute tracking",
        f"F{cfg['feedrate']:.1f}",
        "",
    ]

def gc_skirt(ref_w, ref_h, edge_offset, z_down):
    skirt1_w = ref_w + 2 * edge_offset
    skirt1_h = ref_h + 2 * edge_offset
    x0, x1 = f(-skirt1_w / 2), f(skirt1_w / 2)
    y0, y1 = f(-skirt1_h / 2), f(skirt1_h / 2)
    
    return [
        "; ════════════════════════════════════════════════════════════",
        "; SKIRTING BORDER PASSES",
        "; ════════════════════════════════════════════════════════════",
        f"G0 X{x0} Y{y0}",
        f"G0 Z{z_down:.1f}",
        f"G1 X{x1} Y{y0}",
        f"G1 X{x1} Y{y1}",
        f"G1 X{x0} Y{y1}",
        f"G1 X{x0} Y{y0}",
        "G0 Z0",
        f"G4 P{SKIRT_DWELL_S * 1000}",
    ]

def gc_circles(cfg):
    rows, cols, total = calculate_circle_array(cfg['plate_w'], cfg['plate_h'], cfg['circle_diameter'], cfg['edge_offset'], cfg['circle_gap'])
    num_circles = min(cfg['num_circles'], total)
    
    grid_w = (cols * cfg['circle_diameter']) + ((cols - 1) * cfg['circle_gap'])
    grid_h = (rows * cfg['circle_diameter']) + ((rows - 1) * cfg['circle_gap'])
    
    start_x = -grid_w / 2 + (cfg['circle_diameter'] / 2)
    start_y = -grid_h / 2 + (cfg['circle_diameter'] / 2)
    
    lines = []
    circle_count = 0
    current_motion_time = cfg['motion_time']
    
    for row in range(rows):
        for col in range(cols):
            if circle_count >= num_circles: break
            
            cx = f(start_x + col * (cfg['circle_diameter'] + cfg['circle_gap']))
            cy = f(start_y + row * (cfg['circle_diameter'] + cfg['circle_gap']))
            
            path_length = calculate_spiral_path_length(cfg['circle_diameter'])
            _, speed_mmmin = calculate_speed_from_time(path_length, current_motion_time)
            
            lines.extend([
                "",
                f"; --- Element {circle_count + 1} ---",
                f"G0 X{cx} Y{cy}",
                f"G0 Z{cfg['z_down']:.1f}"
            ])
            
            max_radius = cfg['circle_diameter'] / 2
            num_spirals = 5
            total_degrees = num_spirals * 360
            
            for angle in range(0, total_degrees + 1, 10):
                rad = math.radians(angle)
                current_radius = max_radius * (angle / total_degrees)
                x = cx + current_radius * math.cos(rad)
                y = cy + current_radius * math.sin(rad)
                lines.append(f"G1 X{f(x)} Y{f(y)} F{f(speed_mmmin)}")
                
            lines.append("G0 Z0")
            if circle_count < num_circles - 1:
                lines.append(f"G4 P{cfg['pause_between'] * 1000}")
                
            circle_count += 1
            current_motion_time += cfg['step_time']
    return lines

def gc_serpentine(cfg):
    """Generates continuous sweeping paths inside the offset boundary boundaries"""
    w = cfg['sub_w']
    h = cfg['sub_h']
    
    # Bottom-left base bounds
    x_min, x_max = -w / 2, w / 2
    y_min, y_max = -h / 2, h / 2
    
    step_over = cfg['step_over']
    feedrate = cfg['feedrate']
    num_lines = cfg.get('num_lines', None)  # None = use all
    
    lines = [
        "; ════════════════════════════════════════════════════════════",
        f"; SERPENTINE MOTION: {cfg['pattern'].upper()}",
        "; ════════════════════════════════════════════════════════════"
    ]
    
    if cfg['pattern'] == 'serpentine_x':
        passes = max(1, int(h / step_over) + 1)
        if num_lines is not None:
            passes = min(passes, num_lines)
        lines.extend([f"G0 X{f(x_min)} Y{f(y_min)}", f"G0 Z{cfg['z_down']:.1f}"])
        
        forward = True
        for p in range(passes):
            curr_y = min(y_min + (p * step_over), y_max)
            if p > 0:
                lines.append(f"G1 Y{f(curr_y)} F{f(feedrate)}")
            target_x = x_max if forward else x_min
            lines.append(f"G1 X{f(target_x)} F{f(feedrate)}")
            forward = not forward
            
    else: # serpentine_y
        passes = max(1, int(w / step_over) + 1)
        if num_lines is not None:
            passes = min(passes, num_lines)
        lines.extend([f"G0 X{f(x_min)} Y{f(y_min)}", f"G0 Z{cfg['z_down']:.1f}"])
        
        forward = True
        for p in range(passes):
            curr_x = min(x_min + (p * step_over), x_max)
            if p > 0:
                lines.append(f"G1 X{f(curr_x)} F{f(feedrate)}")
            target_y = y_max if forward else y_min
            lines.append(f"G1 Y{f(target_y)} F{f(feedrate)}")
            forward = not forward
            
    lines.append("G0 Z0")
    return lines

def gc_footer():
    return ["", "G0 Z0      ; safe height", "G0 X0 Y0   ; park", "M84 S0     ; quiet motors", ""]

def build_gcode(cfg):
    gc = gc_header(cfg)
    if cfg['pattern'] == 'circles':
        gc += gc_skirt(cfg['plate_w'], cfg['plate_h'], cfg['edge_offset'], cfg['z_down'])
    else:
        gc += gc_skirt(cfg['sub_w'], cfg['sub_h'], cfg['edge_offset'], cfg['z_down'])
    gc.append("")
    if cfg['pattern'] == 'circles':
        gc += gc_circles(cfg)
    else:
        gc += gc_serpentine(cfg)
    gc += gc_footer()
    return "\n".join(gc)


# ════════════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION FLOW
# ════════════════════════════════════════════════════════════════════════════

def main():
    # Force creation of output directory in the local folder housing this script file
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "═"*68)
    print("  GCode Generator — Low-Velocity Serpentine & Circle Engine")
    print("  Anycubic Mega X Electrochemistry Edition")
    print("═"*68)
    
    # STEP 1: Plate Dimensions
    print("\n[ Step 1 of 6 ]  Plate Dimensions")
    plate_w = prompt_float("  Plate total length X (mm): ")
    plate_h = prompt_float("  Plate total width Y (mm): ")
    
    # STEP 2: Pattern Select
    print("\n[ Step 2 of 6 ]  Pattern Profile Selection")
    print("  1  Circular Array Spirals")
    print("  2  Serpentine Sweeps (Horizontal X-Axis Emphasis)")
    print("  3  Serpentine Sweeps (Vertical Y-Axis Emphasis)")
    choice = prompt_int("  Choose configuration profile [1/2/3]: ", choices=[1, 2, 3])
    pattern = 'circles' if choice == 1 else ('serpentine_x' if choice == 2 else 'serpentine_y')
    
    # STEP 3: Boundary Offsets
    print("\n[ Step 3 of 6 ]  Edge Boundary Margins")
    edge_offset = prompt_float("  Edge offset clear distance (0–10 mm): ", allow_zero=True, max_val=10)
    
    # STEP 4: Mode Specific Geometry Processing
    cfg = {
        'plate_w': plate_w, 'plate_h': plate_h, 
        'edge_offset': edge_offset, 'pattern': pattern
    }
    
    if pattern == 'circles':
        print("\n[ Step 4 of 6 ]  Circle Configuration Matrix")
        circle_gap = prompt_float("  Inter-circle spacing gap (mm) [Enter for 10.0]: ", allow_zero=True, default=10.0)
        circle_diameter = prompt_float("  Element diameter (mm): ")
        
        rows, cols, total = calculate_circle_array(plate_w, plate_h, circle_diameter, edge_offset, circle_gap)
        info_box("Layout Configuration Bound", [
            f"Array Matrix Limits: {rows} Rows x {cols} Columns",
            f"Maximum Target Capacity: {total} circles possible"
        ])
        
        num_circles = prompt_int(f"  Target volume count to drop [1-{total}]: ", min_val=1)
        motion_time = prompt_float("  Allotted deposition run time per node (seconds): ")
        
        path_len = calculate_spiral_path_length(circle_diameter)
        is_valid, _, err = validate_motion_time(motion_time, path_len)
        while not is_valid:
            warn_box("VELOCITY VIOLATION", [err])
            motion_time = prompt_float("  Allotted deposition run time per unit circle (seconds): ", min_val=0.1)
            is_valid, _, err = validate_motion_time(motion_time, path_len)
            
        step_time = prompt_float("  Incremental step scaling time per node (seconds): ", allow_zero=True)
        pause_time = prompt_int("  Delay cooling dwell gap window between elements (seconds): ", min_val=1)
        
        timing = calculate_total_job_time(motion_time, num_circles, int(step_time), pause_time)
        cfg.update({
            'circle_diameter': circle_diameter, 'circle_gap': circle_gap, 'num_circles': num_circles,
            'motion_time': motion_time, 'step_time': step_time, 'pause_between': pause_time,
            'sub_w': plate_w - (2 * edge_offset), 'sub_h': plate_h - (2 * edge_offset)
        })
        
    else:  # Serpentine Paths
        print("\n[ Step 4 of 6 ]  Serpentine Scan Region")

        # ── FIX 1: Sub-region or full plate ──────────────────────────────
        print("  Do you want to scan the entire plate or a smaller sub-region?")
        print("  Sub-region will be centered on the plate (equal margins on all sides).")
        scan_full = prompt_yes_no("  Scan entire plate?")
        if scan_full:
            active_w = plate_w - (2 * edge_offset)
            active_h = plate_h - (2 * edge_offset)
        else:
            print("  Enter sub-region dimensions (must be smaller than plate minus edge offset).")
            max_sub_w = plate_w - (2 * edge_offset)
            max_sub_h = plate_h - (2 * edge_offset)
            active_w = prompt_float(f"  Sub-region width  X (mm, max {max_sub_w:.1f}): ", max_val=max_sub_w)
            active_h = prompt_float(f"  Sub-region height Y (mm, max {max_sub_h:.1f}): ", max_val=max_sub_h)

        # ── FIX 2: Step-over distance ────────────────────────────────────
        print("\n  Track step-over distance — width between lines.")
        step_over = prompt_float("  Distance width between lines (mm): ", allow_zero=False, min_val=0.1)

        # ── FIX 3: Number of lines ───────────────────────────────────────
        if pattern == 'serpentine_x':
            max_lines = max(1, int(active_h / step_over) + 1)
        else:
            max_lines = max(1, int(active_w / step_over) + 1)

        print(f"\n  Number of lines")
        num_lines_input = input(f"  Enter line count [1–{max_lines}, Enter=all {max_lines}]: ").strip()
        if num_lines_input == "":
            num_lines = max_lines
        else:
            try:
                num_lines = max(1, min(int(num_lines_input), max_lines))
            except ValueError:
                num_lines = max_lines
                print(f"  Invalid input — using all {max_lines} lines.")

        path_len = calculate_serpentine_path_length(active_w, active_h, step_over, pattern)

        # ── FIX 4: Feedrate prompt with speed label + confirmation ───────
        MAX_FEEDRATE_MMMIN = ANYCUBIC_MAX_SPEED * 60  # 12000 mm/min

        def speed_label(mms):
            if mms <= 20:   return "🟢 SLOW (safe, good for electrochemistry)"
            elif mms <= 60: return "🟡 MEDIUM (balanced)"
            elif mms <= 100:return "🟠 FAST (check machine condition)"
            elif mms <= 150:return "🔴 VERY FAST (risky, near limit)"
            else:           return "⛔ EXTREME (close to hard ceiling)"

        print("\n  Tool travel speed")
        print("  Enter feedrate (mm/min).")
        print("  Program will show equivalent mm/s + safety info.")
        info_box("Speed reference (Anycubic Mega X — updated ceiling 200 mm/s)", [
            "Minimum (safest)     : 20 mm/s   (1200 mm/min)  — very slow",
            "Recommended (good)   : 40–60 mm/s  (2400–3600 mm/min)  — balanced",
            "Fast (risky)         : 80–150 mm/s  (4800–9000 mm/min)  — high speed",
            "Very fast            : 150–200 mm/s (9000–12000 mm/min) — extreme",
            "",
            "Hard limit (must not exceed): 200 mm/s (12000 mm/min)",
        ])

        while True:
            raw = input("  Feedrate (F value, mm/min): ").strip().replace(",", ".")
            try:
                feedrate_mmmin = float(raw)
            except ValueError:
                print("  ✗  Please enter a valid number."); continue

            speed_mms = feedrate_mmmin / 60

            if feedrate_mmmin <= 0:
                print("  ✗  Must be > 0."); continue

            if feedrate_mmmin > MAX_FEEDRATE_MMMIN:
                warn_box("SPEED EXCEEDS MACHINE LIMIT", [
                    f"You entered: {feedrate_mmmin:.0f} mm/min = {speed_mms:.1f} mm/s",
                    f"Machine max: {ANYCUBIC_MAX_SPEED} mm/s  (hard limit)",
                    "",
                    f"  → Enter a feedrate ≤ {MAX_FEEDRATE_MMMIN:.0f} mm/min",
                ])
                continue

            label = speed_label(speed_mms)
            print(f"  → Feedrate: {feedrate_mmmin:.0f} mm/min = {speed_mms:.1f} mm/s")
            print(f"  {label}")
            if prompt_yes_no("  Keep this speed?"):
                break
            print("  Enter a new feedrate below.")

        # Derive motion_time from feedrate for job time estimate
        motion_time = path_len / (feedrate_mmmin / 60) if feedrate_mmmin > 0 else 0

        timing = calculate_total_job_time(motion_time)
        cfg.update({
            'step_over': step_over,
            'num_lines': num_lines,
            'motion_time': motion_time,
            'feedrate': feedrate_mmmin,
            'speed_mms': feedrate_mmmin / 60,
            'num_circles': 1, 'step_time': 0, 'pause_between': 0,
            'sub_w': active_w, 'sub_h': active_h,
        })
    # Timeline Safety Validation Guardrail
    info_box("Time Analysis Summary", [f"Projected Run Length: {timing['hours']} Hours ({timing['minutes']} Minutes)"])
    if timing['hours'] > DEFAULT_MAX_JOB_DURATION_HOURS:
        warn_box("EXTENDED TIMELINE DETECTED", [f"Execution exceeds standard safety window of {DEFAULT_MAX_JOB_DURATION_HOURS} hours."])
        if not prompt_yes_no("  Proceed with this continuous machine timeline execution structure anyway?"):
            print("\n  Execution terminated to re-adjust settings."); sys.exit(0)

    # STEP 5: Z Depth Working Configuration
    print("\n[ Step 5 of 6 ]  Z Axis Execution Depth Placement")
    print("  Z depth range: -11.0 mm  to  -13.0 mm")
    print("  Select step increment for Z depth values:")
    print("    1  ->  0.2 mm steps  (default)")
    print("    2  ->  0.1 mm steps  (finer control)")
    z_step_raw = input("  Step size [1/2, Enter=default 0.2]: ").strip()
    if z_step_raw == '2':
        z_step = 0.1
        print("  OK  Using 0.1 mm steps")
    else:
        z_step = 0.2
        print("  OK  Using 0.2 mm steps (default)")

    Z_START = -11.0
    Z_END   = -13.0
    steps_n = round((Z_END - Z_START) / (-z_step)) + 1
    available_z = [round(Z_START - i * z_step, 2) for i in range(steps_n)]

    info_box("Available Z Depth Values", [
        f"  Range  : {available_z[0]} mm  to  {available_z[-1]} mm",
        f"  Step   : {z_step} mm",
        f"  Count  : {len(available_z)} positions",
    ])

    while True:
        raw = input(f"  Enter Z depth ({available_z[0]} to {available_z[-1]} mm): ").strip()
        try:
            z_down = round(float(raw), 2)
            if any(abs(z_down - v) < 1e-9 for v in available_z):
                break
            print(f"  X  Must be a {z_step} mm step value between {available_z[0]} and {available_z[-1]}.")
        except ValueError:
            print("  X  Enter a valid number.")
    cfg['z_down'] = z_down

    # STEP 6: Feed Velocity Final Computation
    print("\n[ Step 6 of 6 ]  Velocity Generation Map")
    if pattern == 'circles':
        speed_mms, speed_mmmin = calculate_speed_from_time(path_len, cfg['motion_time'])
        cfg['feedrate'] = speed_mmmin
        cfg['speed_mms'] = speed_mms
        info_box("Dynamic Engine Output", [
            f"Computed Feed Vector Speed: {speed_mms:.2f} mm/s",
            f"Marlin GCode Protocol Value: F{speed_mmmin:.1f} mm/min"
        ])
    else:
        # Serpentine: feedrate already set by user in Step 4
        info_box("Velocity Confirmed", [
            f"User-Set Feed Speed: {cfg['speed_mms']:.2f} mm/s",
            f"Marlin GCode Protocol Value: F{cfg['feedrate']:.1f} mm/min"
        ])

    # File Generation and Export Stage
    gcode_text = build_gcode(cfg)
    move_cnt = sum(1 for l in gcode_text.split("\n") if l.startswith(("G0", "G1")))
    
    out = OUTPUT_FOLDER / f"gcode_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gcode"
    out.write_text(gcode_text)
    
    print("\n" + "═"*68)
    ok_box("EXPORT MATRIX ENVELOPE RECORDED COMPLETE", [
        f"Target Output Path: {out.name}",
        f"Active Move Sequences: {move_cnt} blocks executed",
        f"Assigned Linear Feed Speed: {cfg['speed_mms']:.2f} mm/s"
    ])
    print("═"*68)

    # ════════════════════════════════════════════════════════════════════════════
    #  FINAL EXPORT SUMMARY
    # ════════════════════════════════════════════════════════════════════════════
    def print_summary_line(text: str):
        print(f"  ║  {text:<62}║")

    print("\nFINAL SUMMARY\n")
    print(f"  ╔{'═'*64}╗")
    print_summary_line("✓  Scan sequence")
    print(f"  ╠{'═'*64}╣")
    print_summary_line("1. Tool moves to skirt corner")
    print_summary_line(f"2. Pauses {SKIRT_DWELL_S} seconds (for adjustment)")
    print_summary_line(f"3. Z down to {cfg['z_down']:.1f} mm (working depth)")
    if pattern == 'circles':
        print_summary_line(f"4. Draws {SKIRT_PASSES} skirting rectangle around plate")
        print_summary_line(f"5. Scans {cfg['num_circles']} Circle Spiral nodes")
        print_summary_line(f"   Region: {cfg['sub_w']:.1f} × {cfg['sub_h']:.1f} mm (centered on {cfg['plate_w']:.1f}×{cfg['plate_h']:.1f} plate)")
        print_summary_line(f"   Gap: {cfg['circle_gap']:.1f} mm")
    else:
        print_summary_line(f"4. Draws {SKIRT_PASSES} skirting rectangle around sub-region")
        if pattern == 'serpentine_x':
            passes = max(1, int(cfg['sub_h'] / cfg['step_over']) + 1)
            p_label = "Serpentine X"
        else:
            passes = max(1, int(cfg['sub_w'] / cfg['step_over']) + 1)
            p_label = "Serpentine Y"
        print_summary_line(f"5. Scans {passes} {p_label} lines")
        print_summary_line(f"   Region: {cfg['sub_w']:.1f} × {cfg['sub_h']:.1f} mm (centered on {cfg['plate_w']:.1f}×{cfg['plate_h']:.1f} plate)")
        print_summary_line(f"   Gap: {cfg['step_over']:.1f} mm")
        
    print_summary_line(f"   Speed: {cfg['speed_mms']:.1f} mm/s  (F{cfg['feedrate']:.1f})")
    print_summary_line("6. Z up to 0 mm (safe height)")
    print_summary_line("7. Returns to center origin")
    print(f"  ╚{'═'*64}╝\n")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n\n  Processing interface broken off manually."); sys.exit(0)