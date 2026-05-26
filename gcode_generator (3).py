#!/usr/bin/env python3
"""
GCode Generator — Anycubic Mega X  (XY motion only)
Clear visual output edition
"""
from __future__ import annotations
import math, sys
from pathlib import Path
from datetime import datetime

# ── Machine constants ────────────────────────────────────────────────────────
MEGA_X_MAX_MMS   = 100
MEGA_X_MAX_MMMIN = 6000
MEGA_X_BUILD_X   = 300
MEGA_X_BUILD_Y   = 300
SKIRT_INSET      = 3.0
SKIRT_PASSES     = 2
DWELL_MS         = 60_000   # 60 s


# ════════════════════════════════════════════════════════════════════════════
#  VISUAL HELPERS
# ════════════════════════════════════════════════════════════════════════════

W = 58   # box inner width

def box_line(text="", color=""):
    """One row inside a box, padded to W."""
    return f"  ║  {text:<{W}}║"

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

def sep(c="─", w=62): print(c * w)


# ── ASCII plate diagram ──────────────────────────────────────────────────────

def draw_plate(plate_x, plate_y, scan_x, scan_y, scan_w, scan_h,
               edge_offset, pattern, gap, n_lines, skirting):
    """
    Draw a tiny ASCII top-down view of the plate.
    Plate = outer border, scan area = inner block of fill chars.
    """
    COLS = 40   # diagram width in chars
    ROWS = 20   # diagram height in chars

    def to_col(x): return int(round(x / plate_x * (COLS - 1)))
    def to_row(y): return int(round((1 - y / plate_y) * (ROWS - 1)))  # Y flipped for display

    # Build blank grid
    grid = [[" "] * (COLS + 2) for _ in range(ROWS + 2)]

    # Draw plate border
    for c in range(COLS):
        grid[0][c+1] = "─"
        grid[ROWS][c+1] = "─" if c % 2 == 0 else " "
    for r in range(ROWS):
        grid[r+1][0]      = "│"
        grid[r+1][COLS+1] = "│"
    grid[0][0]       = "┌"; grid[0][COLS+1]    = "┐"
    grid[ROWS][0]    = "└"; grid[ROWS][COLS+1] = "┘"

    # Fill scan area
    sc0 = to_col(scan_x); sc1 = to_col(scan_x + scan_w)
    sr0 = to_row(scan_y + scan_h); sr1 = to_row(scan_y)
    fill = "░" if pattern in (1, 2) else "▒"
    for r in range(sr0, sr1 + 1):
        for c in range(sc0, sc1 + 1):
            if 1 <= r+1 <= ROWS and 1 <= c+1 <= COLS:
                grid[r+1][c+1] = fill

    # Draw scan-area border
    for c in range(sc0, sc1 + 1):
        if 1 <= sr0+1 <= ROWS: grid[sr0+1][c+1] = "─"
        if 1 <= sr1+1 <= ROWS: grid[sr1+1][c+1] = "─"
    for r in range(sr0, sr1 + 1):
        if 1 <= sc0+1 <= COLS: grid[r+1][sc0+1] = "│"
        if 1 <= sc1+1 <= COLS: grid[r+1][sc1+1] = "│"
    if 1 <= sr0+1 <= ROWS and 1 <= sc0+1 <= COLS: grid[sr0+1][sc0+1] = "┌"
    if 1 <= sr0+1 <= ROWS and 1 <= sc1+1 <= COLS: grid[sr0+1][sc1+1] = "┐"
    if 1 <= sr1+1 <= ROWS and 1 <= sc0+1 <= COLS: grid[sr1+1][sc0+1] = "└"
    if 1 <= sr1+1 <= ROWS and 1 <= sc1+1 <= COLS: grid[sr1+1][sc1+1] = "┘"

    # Mark origin (left-front = bottom-left = high row index)
    grid[ROWS][1] = "★"

    print()
    print("  ┌── Plate top-down view ─────────────────────────────────────┐")
    # Print grid top → bottom = plate front (Y=max) → back (Y=0)
    # But Y=0 is "front" (origin), so row ROWS = Y=0 = front = bottom of diagram
    print(f"  │  Y={plate_y:.0f}mm ↑")
    for r, row in enumerate(grid):
        print("  │  " + "".join(row))
    print(f"  │         → X={plate_x:.0f}mm    ★ = origin (left-front corner)")
    pat_sym = {"1": "░ horizontal lines", "2": "░ vertical lines", "3": "▒ diagonal lines"}
    print(f"  │  Fill: {pat_sym.get(str(pattern), '░ scan area')}  │  scan area: {scan_w:.1f}×{scan_h:.1f} mm")
    if skirting:
        print(f"  │  Skirt: 2 rect passes at {SKIRT_INSET} mm inset  +  60s dwell at ★")
    print("  └────────────────────────────────────────────────────────────┘")
    print()


# ════════════════════════════════════════════════════════════════════════════
#  GEOMETRY
# ════════════════════════════════════════════════════════════════════════════

def perp_span(w, h, angle_deg):
    a = math.radians(angle_deg)
    return abs(w * math.sin(a)) + abs(h * math.cos(a))

def max_lines_possible(sw, sh, pattern, gap, angle_deg=45.0):
    span = sh if pattern==1 else sw if pattern==2 else perp_span(sw, sh, angle_deg)
    return max(1, int(span / gap) + 1)

def gap_fits(sw, sh, pattern, gap, angle_deg=45.0):
    span = sh if pattern==1 else sw if pattern==2 else perp_span(sw, sh, angle_deg)
    return gap <= span

def span_label(sw, sh, pattern, angle_deg=45.0):
    if pattern==1: return f"scan height (Y span) = {sh} mm"
    if pattern==2: return f"scan width  (X span) = {sw} mm"
    return f"perpendicular span = {round(perp_span(sw, sh, angle_deg), 2)} mm"

def span_explain(pattern):
    if pattern==1: return "Serpentine X steps in the Y direction"
    if pattern==2: return "Serpentine Y steps in the X direction"
    return "Diagonal lines step perpendicular to the scan angle"


# ── Cohen-Sutherland clip ────────────────────────────────────────────────────

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

def f(n, d=4): return round(n, d)


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
#  GCODE BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def gc_header(cfg):
    pat_names={1:"Serpentine X",2:"Serpentine Y",3:f"Diagonal ({cfg['angle']}°)"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "; ══════════════════════════════════════════════════════",
        f"; GCode — {pat_names[cfg['pattern']]}",
        f"; Plate      : {cfg['plate_x']} × {cfg['plate_y']} mm",
        f"; Edge offset: {cfg['edge_offset']} mm",
        f"; Scan area  : X{cfg['scan_x']}+{cfg['scan_w']}  Y{cfg['scan_y']}+{cfg['scan_h']} mm",
        f"; Gap : {cfg['gap']} mm  Lines: {cfg['n_lines']}  Speed: {cfg['speed_mms']} mm/s",
        f"; Skirting   : {'Yes' if cfg['skirting'] else 'No'}",
        f"; Generated  : {now}",
        "; ══════════════════════════════════════════════════════",
        "G90  ; absolute coords", "G21  ; mm units",
        f"F{cfg['feedrate']:.1f}  ; feedrate in mm/min",
        "G0 X0 Y0  ; start at origin", "",
    ]

def gc_skirt(ox, oy, sw, sh):
    si = SKIRT_INSET
    if sw <= 2*si or sh <= 2*si:
        return ["; skirt skipped — scan area too small"]
    x0,y0 = f(ox+si), f(oy+si)
    x1,y1 = f(ox+sw-si), f(oy+sh-si)
    lines = [
        "; ── SKIRTING ─────────────────────────────────────────",
        f"; Tool moves to left-front corner then waits 60 seconds",
        f"; before drawing 2 rectangular border passes.",
        f"G0 X{x0} Y{y0}  ; go to left-front skirt corner",
        f"G4 P{DWELL_MS}   ; wait 60 seconds (dwell)",
    ]
    for i in range(SKIRT_PASSES):
        lines.append(f"; skirt pass {i+1} of {SKIRT_PASSES}")
        lines += [f"G1 X{x1} Y{y0}",f"G1 X{x1} Y{y1}",
                  f"G1 X{x0} Y{y1}",f"G1 X{x0} Y{y0}"]
    lines.append("; ── END SKIRTING ─────────────────────────────────────")
    return lines

def gc_serpentine_x(ox,oy,sw,sh,gap,n):
    lines=["; ── SCAN LINES (Serpentine X) ────────────────────────",
           "; Each pair: G0 = move to line start, G1 = scan across"]
    for i in range(n):
        y = f(oy + i*gap)
        if y > oy+sh: break
        xs = ox if i%2==0 else ox+sw
        xe = ox+sw if i%2==0 else ox
        dir_label = "→ right" if i%2==0 else "← left"
        lines += [f"G0 X{f(xs)} Y{y}  ; line {i+1}: move to start  (Y={y})",
                  f"G1 X{f(xe)} Y{y}  ; line {i+1}: scan {dir_label}"]
    return lines

def gc_serpentine_y(ox,oy,sw,sh,gap,n):
    lines=["; ── SCAN LINES (Serpentine Y) ────────────────────────",
           "; Each pair: G0 = move to line start, G1 = scan upward/downward"]
    for i in range(n):
        x = f(ox + i*gap)
        if x > ox+sw: break
        ys = oy if i%2==0 else oy+sh
        ye = oy+sh if i%2==0 else oy
        dir_label = "↑ up" if i%2==0 else "↓ down"
        lines += [f"G0 X{x} Y{f(ys)}  ; line {i+1}: move to start  (X={x})",
                  f"G1 X{x} Y{f(ye)}  ; line {i+1}: scan {dir_label}"]
    return lines

def gc_diagonal(ox,oy,sw,sh,gap,n,angle_deg):
    lines=[f"; ── SCAN LINES (Diagonal {angle_deg}°) ───────────────────",
           "; Each pair: G0 = move to line start, G1 = scan diagonally"]
    ar=math.radians(angle_deg); ca,sa=math.cos(ar),math.sin(ar)
    hl=math.hypot(sw,sh)
    for i in range(n):
        mx=ox+i*gap*(-sa); my=oy+i*gap*math.cos(ar)
        p1,p2=clip_line(mx-hl*ca,my-hl*sa,mx+hl*ca,my+hl*sa,ox,ox+sw,oy,oy+sh)
        if p1 is None: continue
        x1,y1=f(p1[0]),f(p1[1]); x2,y2=f(p2[0]),f(p2[1])
        if i%2==1: x1,y1,x2,y2=x2,y2,x1,y1
        lines += [f"G0 X{x1} Y{y1}  ; line {i+1}: move to start",
                  f"G1 X{x2} Y{y2}  ; line {i+1}: scan diagonal"]
    return lines

def gc_footer():
    return ["", "G0 X0 Y0  ; return to origin", "M30       ; end program"]

def build_gcode(cfg):
    gc = gc_header(cfg)
    if cfg['skirting']:
        gc += gc_skirt(cfg['scan_x'],cfg['scan_y'],cfg['scan_w'],cfg['scan_h'])
        gc.append("")
    args=(cfg['scan_x'],cfg['scan_y'],cfg['scan_w'],cfg['scan_h'],cfg['gap'],cfg['n_lines'])
    p=cfg['pattern']
    if p==1: gc+=gc_serpentine_x(*args)
    elif p==2: gc+=gc_serpentine_y(*args)
    else: gc+=gc_diagonal(*args, cfg['angle'])
    gc+=gc_footer()
    return "\n".join(gc)


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    print()
    sep("═")
    print("  GCode Generator — Anycubic Mega X")
    print(f"  Build volume : {MEGA_X_BUILD_X} × {MEGA_X_BUILD_Y} mm")
    print(f"  Speed limit  : {MEGA_X_MAX_MMS} mm/s  ({MEGA_X_MAX_MMMIN} mm/min)")
    sep("═")

    # ── STEP 1: Plate size ───────────────────────────────────────────────────
    print("\n[ Step 1 of 8 ]  Plate dimensions")
    print("  How big is your physical plate?")
    plate_x = prompt_float(f"  Plate width  X (mm, max {MEGA_X_BUILD_X}): ", max_val=float(MEGA_X_BUILD_X))
    plate_y = prompt_float(f"  Plate height Y (mm, max {MEGA_X_BUILD_Y}): ", max_val=float(MEGA_X_BUILD_Y))
    print(f"  → Plate set to: {plate_x} × {plate_y} mm")

    # ── STEP 2: Pattern ──────────────────────────────────────────────────────
    sep()
    print("\n[ Step 2 of 8 ]  Travel pattern")
    print("  How should the tool zigzag across the plate?\n")
    print("  1  Serpentine X  — horizontal lines, tool moves left↔right,")
    print("                     each line is 1 step higher in Y")
    print("  2  Serpentine Y  — vertical lines, tool moves up↕down,")
    print("                     each line is 1 step further in X")
    print("  3  Diagonal      — lines run at an angle (e.g. 45°)")
    pattern = prompt_int("  Choose [1/2/3]: ", choices=[1,2,3])
    angle_deg = 45.0
    if pattern == 3:
        angle_deg = prompt_float("  Diagonal angle in degrees (0–179): ", allow_zero=True, max_val=179.9)
    pat_names={1:"Serpentine X",2:"Serpentine Y",3:f"Diagonal ({angle_deg}°)"}
    print(f"  → Pattern: {pat_names[pattern]}")

    # ── STEP 3: Edge offset ──────────────────────────────────────────────────
    sep()
    print("\n[ Step 3 of 8 ]  Edge offset (safety margin)")
    print("  Stops the tool from travelling right to the plate edge.")
    print("  e.g. offset=10 means the tool won't go closer than 10 mm to any edge.")
    print("  Enter 0 if you want the tool to cover the full plate.")
    max_off = round(min(plate_x, plate_y) / 2.0 - 1.0, 2)
    edge_offset = prompt_float(f"  Edge offset (mm, 0 to {max_off}): ", allow_zero=True, max_val=max_off)
    eff_x = edge_offset;  eff_y = edge_offset
    eff_w = plate_x - 2*edge_offset;  eff_h = plate_y - 2*edge_offset
    print(f"  → Tool will stay inside: {eff_w} × {eff_h} mm area")
    print(f"     (starts at X={eff_x}, Y={eff_y} — {edge_offset} mm from each edge)")

    # ── STEP 4: Sub-region ───────────────────────────────────────────────────
    sep()
    print("\n[ Step 4 of 8 ]  Scan region")
    print(f"  Your full usable area after edge offset is {eff_w} × {eff_h} mm.")
    print("  Do you want to scan only PART of this area?")
    print("  Example: full area is 200×200, but you only need a 50×50 patch.")
    partial = prompt_yes_no("  Scan a sub-region?")
    if partial:
        print(f"\n  Usable area: {eff_w} × {eff_h} mm  (starts at absolute X={eff_x}, Y={eff_y})")
        print("  Enter where your sub-region starts WITHIN this usable area.")
        print("  (0,0) means the front-left corner of the usable area.\n")
        sub_ox = prompt_float(f"  Sub-region start X (0 = left edge,  max {round(eff_w-1,2)}): ",
                              allow_zero=True, max_val=eff_w-1)
        sub_oy = prompt_float(f"  Sub-region start Y (0 = front edge, max {round(eff_h-1,2)}): ",
                              allow_zero=True, max_val=eff_h-1)
        max_sw = round(eff_w - sub_ox, 4)
        max_sh = round(eff_h - sub_oy, 4)
        print(f"\n  Max sub-region size from this start point: {max_sw} × {max_sh} mm")
        sub_w = prompt_float(f"  Sub-region width  (mm, 1 to {max_sw}): ", max_val=max_sw)
        sub_h = prompt_float(f"  Sub-region height (mm, 1 to {max_sh}): ", max_val=max_sh)
        scan_x = eff_x + sub_ox;  scan_y = eff_y + sub_oy
        scan_w = sub_w;           scan_h = sub_h
        print(f"\n  → Sub-region confirmed:")
        print(f"     Width × Height : {scan_w} × {scan_h} mm")
        print(f"     Position on plate: X={scan_x}mm from left, Y={scan_y}mm from front")
    else:
        scan_x,scan_y = eff_x,eff_y
        scan_w,scan_h = eff_w,eff_h
        print(f"  → Full usable area will be scanned: {scan_w} × {scan_h} mm")

    # ── STEP 5: Gap ──────────────────────────────────────────────────────────
    sep()
    print("\n[ Step 5 of 8 ]  Gap between scan lines")
    print("  This is the distance between two consecutive parallel lines.")
    print(f"  Smaller gap = more lines = denser coverage.")
    print(f"  Larger gap  = fewer lines = faster but less coverage.\n")
    print(f"  {span_explain(pattern)}.")
    print(f"  Available span for stepping: {span_label(scan_w, scan_h, pattern, angle_deg)}\n")

    while True:
        gap = prompt_float("  Gap (mm): ")
        if not gap_fits(scan_w, scan_h, pattern, gap, angle_deg):
            warn_box("GAP IS TOO LARGE — NO LINES WOULD FIT", [
                f"Gap you entered  : {gap} mm",
                f"Available span   : {span_label(scan_w, scan_h, pattern, angle_deg)}",
                "",
                "The gap must be smaller than the span the tool steps across.",
                "→ Enter a smaller gap value.",
            ])
        else:
            break

    ml = max_lines_possible(scan_w, scan_h, pattern, gap, angle_deg)
    print()
    info_box("How many lines fit with your current settings?", [
        f"  Scan area  : {scan_w} × {scan_h} mm",
        f"  Pattern    : {pat_names[pattern]}",
        f"  Stepping span: {span_label(scan_w, scan_h, pattern, angle_deg)}",
        f"  Gap        : {gap} mm",
        "",
        f"  ▶  Lines that fit = span ÷ gap + 1  =  {ml} lines",
        "",
        "  This is the MAXIMUM. You can use fewer in the next step.",
        "  You CANNOT enter more — it would go outside the plate.",
    ])

    # ── STEP 6: Number of lines ──────────────────────────────────────────────
    sep()
    print(f"\n[ Step 6 of 8 ]  Number of lines")
    print(f"  Maximum physically possible: {ml} lines")
    print(f"  Press Enter to use all {ml} lines, or type fewer.\n")
    while True:
        raw = input(f"  Lines to generate [1–{ml}, Enter=all]: ").strip()
        if raw == "":
            n_lines = ml
            print(f"  → Using all {ml} lines (full coverage)")
            break
        try:
            n_lines = int(raw)
        except ValueError:
            print("  ✗  Enter a whole number."); continue
        if n_lines < 1:
            print("  ✗  Must be ≥ 1."); continue
        if n_lines > ml:
            warn_box(f"CANNOT GENERATE {n_lines} LINES — HARD LIMIT EXCEEDED", [
                f"  You entered      : {n_lines} lines",
                f"  Maximum allowed  : {ml} lines",
                "",
                f"  Plate  : {plate_x} × {plate_y} mm",
                f"  Scan   : {scan_w} × {scan_h} mm",
                f"  Gap    : {gap} mm",
                "",
                f"  To get more lines → decrease the gap (currently {gap} mm)",
                f"  To use this count → enter a value ≤ {ml}",
            ])
            print()
            continue
        print(f"  → {n_lines} lines chosen  ({round(n_lines*gap,2)} mm coverage)")
        break

    # ── STEP 7: Skirting ─────────────────────────────────────────────────────
    sep()
    print("\n[ Step 7 of 8 ]  Skirting (optional warm-up border)")
    print("  Skirting makes the tool draw 2 rectangles around the")
    print("  scan area BEFORE starting the actual scan lines.")
    print("  Why? It primes/settles the tool and lets you visually check")
    print("  alignment before the real scan begins.")
    print(f"  The tool also pauses 60 seconds at the left-front corner")
    print(f"  so you can inspect it.\n")
    do_skirt = prompt_yes_no("  Enable skirting?")
    if do_skirt and (scan_w <= 2*SKIRT_INSET or scan_h <= 2*SKIRT_INSET):
        print(f"  ⚠  Scan area too small for {SKIRT_INSET} mm skirt — skirting disabled automatically.")
        do_skirt = False
    print(f"  → Skirting: {'ON — 2 border passes + 60s pause' if do_skirt else 'OFF'}")

    # ── STEP 8: Speed ────────────────────────────────────────────────────────
    sep()
    print("\n[ Step 8 of 8 ]  Travel speed")
    print("  How fast should the tool move during scanning?\n")
    info_box("Anycubic Mega X — speed guide", [
        f"  Minimum        : 20 mm/s  (very slow, safest)",
        f"  Recommended    : 60 mm/s  (good balance)",
        f"  Maximum (hard) : 100 mm/s  (absolute machine limit)",
        "",
        "  Above 100 mm/s: motors skip steps, axis shifts occur.",
    ])
    print()
    while True:
        speed_mms = prompt_float("  Speed (mm/s, 1–100): ")
        if speed_mms > MEGA_X_MAX_MMS:
            warn_box(f"SPEED {speed_mms} mm/s EXCEEDS MEGA X HARDWARE LIMIT", [
                f"  You entered  : {speed_mms} mm/s",
                f"  Machine max  : {MEGA_X_MAX_MMS} mm/s  (official Anycubic spec)",
                "",
                "  Exceeding this causes:",
                "    • Missed motor steps → axis position shifts",
                "    • Vibration → bad scan quality",
                "    • Possible driver/motor damage",
                "",
                f"  → Enter a value ≤ {MEGA_X_MAX_MMS} mm/s",
            ])
            print()
            continue
        break
    feedrate = round(speed_mms * 60, 2)
    print(f"  → {speed_mms} mm/s  =  F{feedrate} in GCode")

    # ── BUILD ────────────────────────────────────────────────────────────────
    cfg = {
        "plate_x":plate_x,"plate_y":plate_y,"pattern":pattern,"angle":angle_deg,
        "edge_offset":edge_offset,"scan_x":scan_x,"scan_y":scan_y,
        "scan_w":scan_w,"scan_h":scan_h,"gap":gap,"n_lines":n_lines,
        "speed_mms":speed_mms,"feedrate":feedrate,"skirting":do_skirt,
    }

    # ── VISUAL SUMMARY ───────────────────────────────────────────────────────
    sep("═")
    print("\n  ══ YOUR SCAN SUMMARY ══\n")
    draw_plate(plate_x, plate_y, scan_x, scan_y, scan_w, scan_h,
               edge_offset, pattern, gap, n_lines, do_skirt)

    ok_box("What the GCode will do — in plain English", [
        f"  1. Tool moves to origin (X=0, Y=0)",
        f"  2. Feedrate set to F{feedrate} ({speed_mms} mm/s)",
        *([ f"  3. Tool draws 2 border rectangles around scan area",
            f"     and waits 60 s at left-front corner (skirting ON)"] if do_skirt else
          [ f"  3. Skirting is OFF — tool goes straight to scan"]),
        f"  {'4' if do_skirt else '3'}. Tool scans {n_lines} parallel lines using {pat_names[pattern]}",
        f"     Each line is {gap} mm apart",
        f"     Scan area covers {scan_w} × {scan_h} mm",
        f"     Position on plate: X={scan_x}mm from left, Y={scan_y}mm from front",
        f"  {'5' if do_skirt else '4'}. Tool returns to origin (X=0, Y=0)",
        f"  {'6' if do_skirt else '5'}. Program ends (M30)",
    ])
    print()

    gcode_text = build_gcode(cfg)
    all_lines  = gcode_text.split("\n")
    move_cnt   = sum(1 for l in all_lines if l.startswith(("G0","G1")))

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = pat_names[pattern].replace(" ","_").replace("(","").replace(")","").replace("°","deg")
    out  = Path(f"scan_{slug}_{ts}.gcode")
    out.write_text(gcode_text, encoding="utf-8")

    sep("═")
    print(f"  ✓  Generated {move_cnt} move commands")
    print(f"  ✓  File saved → {out.resolve()}")
    sep("═")

    print("\n  ── GCode preview (first 12 motion lines) ──")
    motion = [l for l in all_lines if l.startswith(("G0","G1","G4"))][:12]
    for l in motion: print(f"  {l}")
    if move_cnt > 12:
        print(f"  … ({move_cnt-12} more motion lines in file)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Aborted."); sys.exit(0)
