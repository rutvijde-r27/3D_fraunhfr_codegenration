#!/usr/bin/env python3
#!/usr/bin/env python3
"""
GCode Generator — Anycubic Mega X  (XY motion only)
Features:
  1. Line count validation with pre-input info box + hard-limit reject loop
  2. Skirting: 2 rect passes at 3mm inset, 60s dwell at left-front corner
  3. Plate edge offset (inset margin)
  4. Partial plate scan (sub-region)
  5. Speed validation against Mega X official max (100 mm/s)
  6. Diagonal serpentine with correct offset-area clipping
"""

from __future__ import annotations
import math
import sys
from pathlib import Path
from datetime import datetime

# ── Machine constants (Anycubic Mega X official specs) ──────────────────────
MEGA_X_MAX_SPEED_MMS   = 100     # mm/s  — official spec: 20~100 mm/s
MEGA_X_MAX_SPEED_MMMIN = 6000    # mm/min
MEGA_X_BUILD_X         = 300     # mm
MEGA_X_BUILD_Y         = 300     # mm
SKIRT_INSET            = 3.0     # mm inset from scan-area boundary for skirt
SKIRT_PASSES           = 2
DWELL_BEFORE_SCAN_MS   = 60_000  # 60 s in milliseconds for G4 P


# ════════════════════════════════════════════════════════════════════════════
#  INPUT HELPERS
# ════════════════════════════════════════════════════════════════════════════

def prompt_float(msg: str, *, allow_zero: bool = False,
                 min_val: float = 0.0, max_val: float | None = None) -> float:
    while True:
        raw = input(msg).strip().replace(",", ".")
        try:
            v = float(raw)
            if allow_zero and v < min_val:
                print(f"  ✗  Must be ≥ {min_val}.")
                continue
            if not allow_zero and v <= min_val:
                print(f"  ✗  Must be > {min_val}.")
                continue
            if max_val is not None and v > max_val:
                print(f"  ✗  Must be ≤ {max_val}.")
                continue
            return v
        except ValueError:
            print("  ✗  Please enter a valid number.")


def prompt_int(msg: str, *, choices: list[int] | None = None,
               min_val: int = 1) -> int:
    while True:
        raw = input(msg).strip()
        try:
            v = int(raw)
            if choices and v not in choices:
                print(f"  ✗  Choose one of: {choices}")
                continue
            if v < min_val:
                print(f"  ✗  Must be ≥ {min_val}.")
                continue
            return v
        except ValueError:
            print("  ✗  Please enter a whole number.")


def prompt_yes_no(msg: str) -> bool:
    while True:
        r = input(f"{msg} [y/n]: ").strip().lower()
        if r in ("y", "yes"): return True
        if r in ("n", "no"):  return False
        print("  ✗  Enter y or n.")


def sep(char: str = "─", w: int = 60) -> None:
    print(char * w)


# ════════════════════════════════════════════════════════════════════════════
#  BOX PRINTERS
# ════════════════════════════════════════════════════════════════════════════

W = 54  # inner width for all boxes

def _pad(s: str) -> str:
    return f"  ║  {s:<{W}}║"

def info_box(title: str, rows: list[str]) -> None:
    print(f"  ╔{'═'*W}╗")
    print(f"  ║  {('✦  ' + title):<{W}}║")
    print(f"  ╠{'═'*W}╣")
    for r in rows:
        print(_pad(r))
    print(f"  ╚{'═'*W}╝")


def warn_box(title: str, rows: list[str]) -> None:
    print(f"  ╔{'═'*W}╗")
    print(f"  ║  {'✗  ' + title:<{W}}║")
    print(f"  ╠{'═'*W}╣")
    for r in rows:
        print(_pad(r))
    print(f"  ╚{'═'*W}╝")


# ════════════════════════════════════════════════════════════════════════════
#  GEOMETRY
# ════════════════════════════════════════════════════════════════════════════

def perp_span(w: float, h: float, angle_deg: float) -> float:
    a = math.radians(angle_deg)
    return abs(w * math.sin(a)) + abs(h * math.cos(a))


def max_lines_possible(sw: float, sh: float, pattern: int,
                        gap: float, angle_deg: float = 45.0) -> int:
    if pattern == 1:   span = sh
    elif pattern == 2: span = sw
    else:              span = perp_span(sw, sh, angle_deg)
    return max(1, int(span / gap) + 1)


def gap_fits(sw: float, sh: float, pattern: int,
             gap: float, angle_deg: float = 45.0) -> bool:
    if pattern == 1:   return gap <= sh
    elif pattern == 2: return gap <= sw
    else:              return gap <= perp_span(sw, sh, angle_deg)


def span_label(sw: float, sh: float, pattern: int,
               angle_deg: float = 45.0) -> str:
    if pattern == 1:   return f"scan height = {sh} mm"
    elif pattern == 2: return f"scan width = {sw} mm"
    else:
        return f"perpendicular span = {round(perp_span(sw, sh, angle_deg), 3)} mm"


# ── Cohen-Sutherland line clip ──────────────────────────────────────────────

def clip_line(x1, y1, x2, y2, xn, xx, yn, yx):
    I, L, R, B, T = 0, 1, 2, 4, 8

    def reg(x, y):
        c = 0
        if x < xn:   c |= L
        elif x > xx: c |= R
        if y < yn:   c |= B
        elif y > yx: c |= T
        return c

    c1, c2 = reg(x1, y1), reg(x2, y2)
    for _ in range(20):
        if not (c1 | c2): return (x1, y1), (x2, y2)
        if c1 & c2:       return None, None
        co = c1 or c2
        if co & T:
            x = x1 + (x2 - x1) * (yx - y1) / (y2 - y1) if y2 != y1 else x1; y = yx
        elif co & B:
            x = x1 + (x2 - x1) * (yn - y1) / (y2 - y1) if y2 != y1 else x1; y = yn
        elif co & R:
            y = y1 + (y2 - y1) * (xx - x1) / (x2 - x1) if x2 != x1 else y1; x = xx
        else:
            y = y1 + (y2 - y1) * (xn - x1) / (x2 - x1) if x2 != x1 else y1; x = xn
        if co == c1: x1, y1, c1 = x, y, reg(x, y)
        else:        x2, y2, c2 = x, y, reg(x, y)
    return None, None


def f(n: float, d: int = 4) -> float:
    return round(n, d)


# ════════════════════════════════════════════════════════════════════════════
#  GCODE SECTION BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def section_header(cfg: dict) -> list[str]:
    pat_names = {1: "Serpentine X", 2: "Serpentine Y",
                 3: f"Diagonal ({cfg['angle']}°)"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "; ═══════════════════════════════════════════════════",
        "; GCode — Plate Scanning",
        f"; Machine    : Anycubic Mega X",
        f"; Pattern    : {pat_names[cfg['pattern']]}",
        f"; Plate      : {cfg['plate_x']} × {cfg['plate_y']} mm",
        f"; Edge offset: {cfg['edge_offset']} mm",
        f"; Scan area  : X{cfg['scan_x']}+{cfg['scan_w']}  Y{cfg['scan_y']}+{cfg['scan_h']} mm",
        f"; Gap        : {cfg['gap']} mm  |  Lines: {cfg['n_lines']}",
        f"; Speed      : {cfg['speed_mms']} mm/s  ({cfg['feedrate']} mm/min)",
        f"; Skirting   : {'Yes — 2 passes, 60s dwell' if cfg['skirting'] else 'No'}",
        f"; Generated  : {now}",
        "; ═══════════════════════════════════════════════════",
        "G90          ; Absolute positioning",
        "G21          ; Units: mm",
        f"F{cfg['feedrate']:.1f}  ; Feedrate",
        "G0 X0 Y0     ; Home to origin",
        "",
    ]


def section_skirt(ox: float, oy: float, sw: float, sh: float) -> list[str]:
    """2-pass rectangular skirt SKIRT_INSET mm inside the scan boundary."""
    si = SKIRT_INSET
    if sw <= 2 * si or sh <= 2 * si:
        return ["; ⚠ Skirt skipped — scan area too small for skirt inset"]

    x0 = f(ox + si);  y0 = f(oy + si)
    x1 = f(ox + sw - si); y1 = f(oy + sh - si)

    lines = [
        "; ─── Skirting ────────────────────────────────",
        f"; {SKIRT_PASSES} passes at {si} mm inset from scan boundary",
        f"; Left-front corner dwell: {DWELL_BEFORE_SCAN_MS // 1000} s",
        f"G0 X{x0} Y{y0}    ; → left-front corner of skirt",
        f"G4 P{DWELL_BEFORE_SCAN_MS}  ; wait {DWELL_BEFORE_SCAN_MS // 1000} seconds",
    ]
    for i in range(SKIRT_PASSES):
        lines.append(f"; skirt pass {i + 1}")
        lines += [
            f"G1 X{x1} Y{y0}",
            f"G1 X{x1} Y{y1}",
            f"G1 X{x0} Y{y1}",
            f"G1 X{x0} Y{y0}",
        ]
    lines.append("; ─── End Skirting ────────────────────────────")
    return lines


def section_serpentine_x(ox, oy, sw, sh, gap, n_lines) -> list[str]:
    lines = ["; ─── Serpentine X (lines along X, stepping in Y) ───"]
    for i in range(n_lines):
        y = f(oy + i * gap)
        if y > oy + sh: break
        xs = ox if i % 2 == 0 else ox + sw
        xe = ox + sw if i % 2 == 0 else ox
        lines += [f"G0 X{f(xs)} Y{y}  ; line {i+1} start",
                  f"G1 X{f(xe)} Y{y}  ; line {i+1} end"]
    return lines


def section_serpentine_y(ox, oy, sw, sh, gap, n_lines) -> list[str]:
    lines = ["; ─── Serpentine Y (lines along Y, stepping in X) ───"]
    for i in range(n_lines):
        x = f(ox + i * gap)
        if x > ox + sw: break
        ys = oy if i % 2 == 0 else oy + sh
        ye = oy + sh if i % 2 == 0 else oy
        lines += [f"G0 X{x} Y{f(ys)}  ; line {i+1} start",
                  f"G1 X{x} Y{f(ye)}  ; line {i+1} end"]
    return lines


def section_diagonal(ox, oy, sw, sh, gap, n_lines, angle_deg) -> list[str]:
    lines = [f"; ─── Diagonal Serpentine {angle_deg}° ─────────────────"]
    ar = math.radians(angle_deg)
    ca, sa = math.cos(ar), math.sin(ar)
    hl = math.hypot(sw, sh)
    for i in range(n_lines):
        # perpendicular offset from (ox, oy)
        mx = ox + i * gap * (-sa)
        my = oy + i * gap * math.cos(ar)
        p1, p2 = clip_line(mx - hl * ca, my - hl * sa,
                            mx + hl * ca, my + hl * sa,
                            ox, ox + sw, oy, oy + sh)
        if p1 is None or p2 is None:
            continue
        x1, y1 = f(p1[0]), f(p1[1])
        x2, y2 = f(p2[0]), f(p2[1])
        if i % 2 == 1:
            x1, y1, x2, y2 = x2, y2, x1, y1
        lines += [f"G0 X{x1} Y{y1}  ; line {i+1} start",
                  f"G1 X{x2} Y{y2}  ; line {i+1} end"]
    return lines


def section_footer() -> list[str]:
    return ["", "G0 X0 Y0     ; Return to origin", "M30          ; End program"]


def build_gcode(cfg: dict) -> str:
    gc: list[str] = []
    gc += section_header(cfg)

    if cfg['skirting']:
        gc += section_skirt(cfg['scan_x'], cfg['scan_y'],
                             cfg['scan_w'], cfg['scan_h'])
        gc.append("")

    pat = cfg['pattern']
    args = (cfg['scan_x'], cfg['scan_y'],
            cfg['scan_w'], cfg['scan_h'],
            cfg['gap'], cfg['n_lines'])

    if pat == 1:   gc += section_serpentine_x(*args)
    elif pat == 2: gc += section_serpentine_y(*args)
    else:          gc += section_diagonal(*args, cfg['angle'])

    gc += section_footer()
    return "\n".join(gc)


# ════════════════════════════════════════════════════════════════════════════
#  MAIN INTERACTIVE FLOW
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print()
    sep("═")
    print("  GCode Generator — Anycubic Mega X")
    print(f"  Build volume : {MEGA_X_BUILD_X} × {MEGA_X_BUILD_Y} mm")
    print(f"  Speed limit  : {MEGA_X_MAX_SPEED_MMS} mm/s  ({MEGA_X_MAX_SPEED_MMMIN} mm/min)")
    sep("═")
    print()

    # ────────────────────────────────────────────────────────────────────────
    # STEP 1 — Plate dimensions
    # ────────────────────────────────────────────────────────────────────────
    print("[ Step 1 ]  Plate dimensions")
    plate_x = prompt_float(
        f"  Plate width  X (mm, max {MEGA_X_BUILD_X}): ",
        max_val=float(MEGA_X_BUILD_X))
    plate_y = prompt_float(
        f"  Plate height Y (mm, max {MEGA_X_BUILD_Y}): ",
        max_val=float(MEGA_X_BUILD_Y))
    print(f"  → Plate: {plate_x} × {plate_y} mm\n")

    # ────────────────────────────────────────────────────────────────────────
    # STEP 2 — Pattern
    # ────────────────────────────────────────────────────────────────────────
    sep()
    print("[ Step 2 ]  Travel pattern")
    print("  1  Serpentine X   (lines along X, step in Y)")
    print("  2  Serpentine Y   (lines along Y, step in X)")
    print("  3  Diagonal Serpentine")
    pattern = prompt_int("  Choose [1/2/3]: ", choices=[1, 2, 3])
    angle_deg = 45.0
    if pattern == 3:
        angle_deg = prompt_float(
            "  Diagonal angle in degrees (0–179): ",
            allow_zero=True, max_val=179.9)
    pat_names = {1: "Serpentine X", 2: "Serpentine Y",
                 3: f"Diagonal ({angle_deg}°)"}
    print(f"  → {pat_names[pattern]}\n")

    # ────────────────────────────────────────────────────────────────────────
    # STEP 3 — Edge offset
    # ────────────────────────────────────────────────────────────────────────
    sep()
    print("[ Step 3 ]  Plate edge offset  (inset margin)")
    print("  Keeps the tool away from plate edges. Enter 0 for none.")
    max_offset = round(min(plate_x, plate_y) / 2.0 - 1.0, 2)
    edge_offset = prompt_float(
        f"  Edge offset (mm, 0 to {max_offset}): ",
        allow_zero=True, max_val=max_offset)
    eff_x = edge_offset
    eff_y = edge_offset
    eff_w = plate_x - 2 * edge_offset
    eff_h = plate_y - 2 * edge_offset
    print(f"  → Effective area: X{eff_x}+{eff_w}  Y{eff_y}+{eff_h} mm\n")

    # ────────────────────────────────────────────────────────────────────────
    # STEP 4 — Partial scan region
    # ────────────────────────────────────────────────────────────────────────
    sep()
    print("[ Step 4 ]  Scan region")
    partial = prompt_yes_no("  Scan only a sub-region of the effective area?")
    if partial:
        print(f"  Available effective area: {eff_w} × {eff_h} mm")
        print(f"  Origin of effective area: X={eff_x}, Y={eff_y}")
        print("  Enter sub-region as offset FROM the effective area origin.\n")
        sub_ox = prompt_float(
            f"  Sub-region X start (0 to {round(eff_w - 1, 2)}): ",
            allow_zero=True, max_val=eff_w - 1)
        sub_oy = prompt_float(
            f"  Sub-region Y start (0 to {round(eff_h - 1, 2)}): ",
            allow_zero=True, max_val=eff_h - 1)
        max_sw = round(eff_w - sub_ox, 4)
        max_sh = round(eff_h - sub_oy, 4)
        sub_w = prompt_float(f"  Sub-region width  (1 to {max_sw}): ", max_val=max_sw)
        sub_h = prompt_float(f"  Sub-region height (1 to {max_sh}): ", max_val=max_sh)
        scan_x = eff_x + sub_ox
        scan_y = eff_y + sub_oy
        scan_w = sub_w
        scan_h = sub_h
        print(f"  → Scan region (absolute): X{scan_x}+{scan_w}  Y{scan_y}+{scan_h} mm\n")
    else:
        scan_x, scan_y = eff_x, eff_y
        scan_w, scan_h = eff_w, eff_h
        print(f"  → Full effective area: {scan_w} × {scan_h} mm\n")

    # ────────────────────────────────────────────────────────────────────────
    # STEP 5 — Gap  (with immediate fit check)
    # ────────────────────────────────────────────────────────────────────────
    sep()
    print("[ Step 5 ]  Line spacing (gap)")
    while True:
        gap = prompt_float("  Gap between consecutive lines (mm): ")
        if not gap_fits(scan_w, scan_h, pattern, gap, angle_deg):
            sl = span_label(scan_w, scan_h, pattern, angle_deg)
            warn_box("GAP EXCEEDS SCAN AREA", [
                f"Gap entered    : {gap} mm",
                f"Available span : {sl}",
                "",
                "No lines can fit with this gap.",
                "→ Decrease the gap and try again.",
            ])
            print()
        else:
            break

    ml = max_lines_possible(scan_w, scan_h, pattern, gap, angle_deg)
    print()
    info_box("Lines possible with your current settings", [
        f"Scan area  : {scan_w} × {scan_h} mm",
        f"Pattern    : {pat_names[pattern]}",
        f"Gap        : {gap} mm",
        "",
        f"  ▶  Maximum lines that fit : {ml}",
        "",
        "This is the physical limit for these settings.",
        "You cannot enter more than this in the next step.",
    ])
    print()

    # ────────────────────────────────────────────────────────────────────────
    # STEP 6 — Number of lines  (hard-limit loop — NEVER accepts > ml)
    # ────────────────────────────────────────────────────────────────────────
    sep()
    print("[ Step 6 ]  Number of lines")
    print(f"  Physical maximum with gap {gap} mm: {ml} lines")
    while True:
        raw = input(f"  Enter line count  [press Enter to use all {ml}]: ").strip()
        if raw == "":
            n_lines = ml
            print(f"  → Using all {ml} lines")
            break
        try:
            n_lines = int(raw)
        except ValueError:
            print("  ✗  Please enter a whole number.")
            continue

        if n_lines < 1:
            print("  ✗  Must be ≥ 1.")
            continue

        if n_lines > ml:
            warn_box("HARD LIMIT EXCEEDED — input rejected", [
                f"You entered    : {n_lines} lines",
                f"Maximum allowed: {ml} lines",
                "",
                f"Plate          : {plate_x} × {plate_y} mm",
                f"Scan area      : {scan_w} × {scan_h} mm",
                f"Gap            : {gap} mm",
                "",
                f"→ Enter a value ≤ {ml}",
                "  OR go back and decrease the gap.",
            ])
            print()
            continue  # loops — NEVER accepts the bad value

        break  # only reaches here if 1 ≤ n_lines ≤ ml

    print(f"  → Lines to generate: {n_lines}\n")

    # ────────────────────────────────────────────────────────────────────────
    # STEP 7 — Skirting
    # ────────────────────────────────────────────────────────────────────────
    sep()
    print("[ Step 7 ]  Skirting")
    print(f"  Draws {SKIRT_PASSES} rectangular passes at {SKIRT_INSET} mm inset")
    print("  from the scan area boundary.")
    print(f"  Pauses {DWELL_BEFORE_SCAN_MS // 1000} s at left-front corner before scan starts.")
    do_skirt = prompt_yes_no("  Enable skirting?")
    if do_skirt and (scan_w <= 2 * SKIRT_INSET or scan_h <= 2 * SKIRT_INSET):
        print(f"  ⚠  Scan area too small for {SKIRT_INSET} mm skirt inset — skirting disabled.")
        do_skirt = False
    print(f"  → Skirting: {'ON' if do_skirt else 'OFF'}\n")

    # ────────────────────────────────────────────────────────────────────────
    # STEP 8 — Travel speed  (hard limit: Mega X 100 mm/s)
    # ────────────────────────────────────────────────────────────────────────
    sep()
    print("[ Step 8 ]  Travel speed")
    info_box("Anycubic Mega X speed reference", [
        f"Official max print speed : {MEGA_X_MAX_SPEED_MMS} mm/s",
        f"                         = {MEGA_X_MAX_SPEED_MMMIN} mm/min",
        f"Recommended (best quality): 60 mm/s",
        f"Minimum sensible speed   : 20 mm/s",
    ])
    print()
    while True:
        speed_mms = prompt_float("  Enter speed (mm/s): ")
        if speed_mms > MEGA_X_MAX_SPEED_MMS:
            warn_box("SPEED EXCEEDS MEGA X MAXIMUM", [
                f"You entered  : {speed_mms} mm/s",
                f"Machine max  : {MEGA_X_MAX_SPEED_MMS} mm/s  (official spec)",
                "",
                "Consequences of exceeding the limit:",
                "  • Missed steps / axis shift",
                "  • Motor / driver overheating",
                "  • Degraded scan / print quality",
                "  • Possible mechanical damage",
                "",
                f"→ Enter a value ≤ {MEGA_X_MAX_SPEED_MMS} mm/s",
            ])
            print()
            continue
        break

    feedrate = round(speed_mms * 60, 2)
    print(f"  → Speed: {speed_mms} mm/s  →  {feedrate} mm/min (GCode F value)\n")

    # ────────────────────────────────────────────────────────────────────────
    # BUILD & SAVE
    # ────────────────────────────────────────────────────────────────────────
    cfg = {
        "plate_x":     plate_x,
        "plate_y":     plate_y,
        "pattern":     pattern,
        "angle":       angle_deg,
        "edge_offset": edge_offset,
        "scan_x":      scan_x,
        "scan_y":      scan_y,
        "scan_w":      scan_w,
        "scan_h":      scan_h,
        "gap":         gap,
        "n_lines":     n_lines,
        "speed_mms":   speed_mms,
        "feedrate":    feedrate,
        "skirting":    do_skirt,
    }

    sep("═")
    print("  Generating GCode …")
    gcode_text = build_gcode(cfg)
    all_lines  = gcode_text.split("\n")
    move_cnt   = sum(1 for l in all_lines if l.startswith(("G0", "G1")))

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = pat_names[pattern].replace(" ", "_").replace("(", "").replace(")", "").replace("°", "deg")
    
    # 1. Find the repository folder where this script lives
    repo_dir = Path(__file__).parent.resolve()
    output_dir = repo_dir / "output"
    
    # 2. Create the 'output' folder if it doesn't exist yet
    output_dir.mkdir(exist_ok=True)
    
    # 3. Direct the G-code file inside the output folder
    out = output_dir / f"scan_{slug}_{ts}.gcode"
    
    out.write_text(gcode_text, encoding="utf-8")

    print(f"\n  ✓  {move_cnt} move commands")
    print(f"  ✓  Saved → {out.resolve()}")
    sep("═")

    print("\n  ── GCode preview (first 15 motion lines) ──")
    motion = [l for l in all_lines if l.startswith(("G0", "G1"))][:15]
    for l in motion:
        print(f"  {l}")
    if move_cnt > 15:
        print(f"  … ({move_cnt - 15} more motion lines in file)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Aborted by user.")
        sys.exit(0)


    
   
    

