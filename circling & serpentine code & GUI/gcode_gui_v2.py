#!/usr/bin/env python3
"""
GCode Generator GUI — Anycubic Mega X Electrochemistry
Supports: Circular Spiral Array  |  Serpentine X  |  Serpentine Y
Built on circle_gcode_mergedv3 logic — customtkinter wizard UI
"""
import math, sys
from pathlib import Path
from datetime import datetime
import customtkinter as ctk

# ════════════════════════════════════════════════════════════════════════════
#  MACHINE CONSTANTS  (must match CLI script)
# ════════════════════════════════════════════════════════════════════════════
LOGICAL_ORIGIN_X = 150
LOGICAL_ORIGIN_Y = 150
LOGICAL_ORIGIN_Z = 120

MEGA_X_BUILD_X = 300
MEGA_X_BUILD_Y = 300

ANYCUBIC_MIN_SPEED =   1    # mm/s
ANYCUBIC_MAX_SPEED = 200    # mm/s  (raised ceiling)

Z_DOWN_MAX        = -11.0   # user-selectable start
Z_DOWN_HARD_LIMIT = -13.0   # hard floor

SKIRT_DWELL_S = 90
SKIRT_PASSES  = 1

OUTPUT_FOLDER: Path = Path(__file__).parent.resolve() / "GCode_Generated_Output"

DEFAULT_PAUSE_BETWEEN_CIRCLES = 10


# ════════════════════════════════════════════════════════════════════════════
#  GEOMETRY & MATH  (copy from CLI script)
# ════════════════════════════════════════════════════════════════════════════
def f(n, d=4): return round(n, d)

def calculate_circle_array(plate_w, plate_h, circle_diameter, edge_offset, circle_gap):
    effective_w = plate_w - (2 * edge_offset)
    effective_h = plate_h - (2 * edge_offset)
    cols = max(1, int((effective_w + circle_gap) / (circle_diameter + circle_gap)))
    rows = max(1, int((effective_h + circle_gap) / (circle_diameter + circle_gap)))
    return rows, cols, rows * cols

def calculate_spiral_path_length(diameter, num_spirals=5):
    return math.pi * (diameter / 2) * num_spirals

def calculate_serpentine_path_length(w, h, step_over, mode):
    if mode == 'serpentine_x':
        passes = max(1, int(h / step_over) + 1)
        return passes * w + (passes - 1) * step_over
    else:
        passes = max(1, int(w / step_over) + 1)
        return passes * h + (passes - 1) * step_over

def calculate_total_job_time(base_motion_s, num_elements=1, step_increment_s=0,
                              pause_between_s=0, skirting_s=60):
    total_motion = sum(base_motion_s + step_increment_s * i for i in range(num_elements))
    total_pauses = max(0, num_elements - 1) * pause_between_s
    total_s = skirting_s + total_motion + total_pauses + num_elements * 2
    return {'seconds': int(total_s),
            'minutes': round(total_s / 60, 1),
            'hours':   round(total_s / 3600, 2)}

def speed_label(mms):
    if   mms <=  20: return "🟢 SLOW — safe, ideal for electrochemistry"
    elif mms <=  60: return "🟡 MEDIUM — balanced"
    elif mms <= 100: return "🟠 FAST — check machine condition"
    elif mms <= 150: return "🔴 VERY FAST — risky, near limit"
    else:            return "⛔ EXTREME — close to hard ceiling"


# ════════════════════════════════════════════════════════════════════════════
#  GCODE BUILDERS  (copy from CLI script)
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
        "", "G21  ; metric standard", "G90  ; absolute tracking",
        f"F{cfg['feedrate']:.1f}", "",
    ]

def gc_skirt(ref_w, ref_h, edge_offset, z_down):
    s_w = ref_w + 2 * edge_offset
    s_h = ref_h + 2 * edge_offset
    x0, x1 = f(-s_w/2), f(s_w/2)
    y0, y1 = f(-s_h/2), f(s_h/2)
    return [
        "; ════════════════════════════════════════════════════════════",
        "; SKIRTING BORDER PASSES",
        "; ════════════════════════════════════════════════════════════",
        f"G0 X{x0} Y{y0}", f"G0 Z{z_down:.1f}",
        f"G1 X{x1} Y{y0}", f"G1 X{x1} Y{y1}",
        f"G1 X{x0} Y{y1}", f"G1 X{x0} Y{y0}",
        "G0 Z0", f"G4 P{SKIRT_DWELL_S * 1000}",
    ]

def gc_circles(cfg):
    rows, cols, total = calculate_circle_array(
        cfg['plate_w'], cfg['plate_h'],
        cfg['circle_diameter'], cfg['edge_offset'], cfg['circle_gap'])
    num_circles = min(cfg['num_circles'], total)
    grid_w = cols * cfg['circle_diameter'] + (cols-1) * cfg['circle_gap']
    grid_h = rows * cfg['circle_diameter'] + (rows-1) * cfg['circle_gap']
    start_x = -grid_w/2 + cfg['circle_diameter']/2
    start_y = -grid_h/2 + cfg['circle_diameter']/2

    lines = []
    circle_count = 0
    cur_time = cfg['motion_time']

    for row in range(rows):
        for col in range(cols):
            if circle_count >= num_circles: break
            cx = f(start_x + col * (cfg['circle_diameter'] + cfg['circle_gap']))
            cy = f(start_y + row * (cfg['circle_diameter'] + cfg['circle_gap']))
            path_len  = calculate_spiral_path_length(cfg['circle_diameter'])
            speed_mmmin = (path_len / cur_time) * 60 if cur_time > 0 else 600
            lines.extend(["", f"; --- Element {circle_count+1} ---",
                           f"G0 X{cx} Y{cy}", f"G0 Z{cfg['z_down']:.1f}"])
            max_r = cfg['circle_diameter'] / 2
            total_deg = 5 * 360
            for angle in range(0, total_deg+1, 10):
                rad = math.radians(angle)
                r = max_r * (angle / total_deg)
                lines.append(f"G1 X{f(cx+r*math.cos(rad))} Y{f(cy+r*math.sin(rad))} F{f(speed_mmmin)}")
            lines.append("G0 Z0")
            if circle_count < num_circles - 1:
                lines.append(f"G4 P{cfg['pause_between'] * 1000}")
            circle_count += 1
            cur_time += cfg['step_time']
    return lines

def gc_serpentine(cfg):
    w, h = cfg['sub_w'], cfg['sub_h']
    x_min, x_max = -w/2, w/2
    y_min, y_max = -h/2, h/2
    step_over  = cfg['step_over']
    feedrate   = cfg['feedrate']
    num_lines  = cfg.get('num_lines', None)

    lines = [
        "; ════════════════════════════════════════════════════════════",
        f"; SERPENTINE MOTION: {cfg['pattern'].upper()}",
        "; ════════════════════════════════════════════════════════════"
    ]
    if cfg['pattern'] == 'serpentine_x':
        passes = max(1, int(h/step_over)+1)
        if num_lines: passes = min(passes, num_lines)
        lines.extend([f"G0 X{f(x_min)} Y{f(y_min)}", f"G0 Z{cfg['z_down']:.1f}"])
        fwd = True
        for p in range(passes):
            cy = min(y_min + p*step_over, y_max)
            if p > 0: lines.append(f"G1 Y{f(cy)} F{f(feedrate)}")
            lines.append(f"G1 X{f(x_max if fwd else x_min)} F{f(feedrate)}")
            fwd = not fwd
    else:
        passes = max(1, int(w/step_over)+1)
        if num_lines: passes = min(passes, num_lines)
        lines.extend([f"G0 X{f(x_min)} Y{f(y_min)}", f"G0 Z{cfg['z_down']:.1f}"])
        fwd = True
        for p in range(passes):
            cx = min(x_min + p*step_over, x_max)
            if p > 0: lines.append(f"G1 X{f(cx)} F{f(feedrate)}")
            lines.append(f"G1 Y{f(y_max if fwd else y_min)} F{f(feedrate)}")
            fwd = not fwd
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
#  GUI APPLICATION
# ════════════════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

TOTAL_STEPS_CIRCLES    = 6
TOTAL_STEPS_SERPENTINE = 5

PAT_LABELS = {
    'circles':     'Circular Array Spirals',
    'serpentine_x':'Serpentine Sweeps — Horizontal (X)',
    'serpentine_y':'Serpentine Sweeps — Vertical (Y)',
}

class GCodeWizardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GCode Generator — Anycubic Mega X  ✦  Electrochemistry Edition")
        self.geometry("600x700")
        self.resizable(False, False)

        # ── default config ────────────────────────────────────────────────
        self.cfg = {
            'plate_w': 100.0, 'plate_h': 100.0,
            'edge_offset': 2.0,
            'pattern': 'serpentine_x',
            # serpentine defaults
            'scan_full': True,
            'sub_w': 100.0, 'sub_h': 100.0,
            'step_over': 4.0,
            'num_lines': None,
            'feedrate': 2400.0, 'speed_mms': 40.0,
            # circle defaults
            'circle_diameter': 10.0, 'circle_gap': 10.0,
            'num_circles': 1, 'motion_time': 30.0,
            'step_time': 0.0, 'pause_between': 10,
            # shared
            'z_down': -11.0,
        }
        self.current_step = 1
        self._max_lines = 1

        # ── layout ────────────────────────────────────────────────────────
        self.view_frame = ctk.CTkFrame(self, corner_radius=12)
        self.view_frame.pack(padx=24, pady=20, fill="both", expand=True)

        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=24, pady=(0, 18))

        self.btn_back = ctk.CTkButton(self.nav_frame, text="◀  Back",
                                      command=self.prev_step, state="disabled", width=120)
        self.btn_back.pack(side="left")

        self.lbl_step = ctk.CTkLabel(self.nav_frame, text="Step 1",
                                     font=("Arial", 13, "bold"))
        self.lbl_step.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(self.nav_frame, text="Next  ▶",
                                      command=self.next_step, width=120)
        self.btn_next.pack(side="right")

        self.show_step()

    # ── navigation ────────────────────────────────────────────────────────
    def _total_steps(self):
        p = self.cfg.get('pattern','serpentine_x')
        return TOTAL_STEPS_CIRCLES if p == 'circles' else TOTAL_STEPS_SERPENTINE

    def show_step(self):
        for w in self.view_frame.winfo_children():
            w.destroy()
        total = self._total_steps()
        self.lbl_step.configure(text=f"Step {self.current_step} of {total}")
        self.btn_back.configure(state="normal" if self.current_step > 1 else "disabled")
        self.btn_next.configure(
            text="✦  Generate GCode" if self.current_step == total else "Next  ▶")

        dispatch = {
            1: self._step_plate,
            2: self._step_pattern,
            3: self._step_circles if self.cfg['pattern']=='circles' else self._step_serp_region,
            4: self._step_circle_timing if self.cfg['pattern']=='circles' else self._step_serp_lines,
            5: self._step_z if self.cfg['pattern']=='circles' else self._step_serp_speed,
            6: self._step_summary,
        }
        dispatch[self.current_step]()

    def next_step(self):
        handlers = {
            1: self._save_plate,
            2: self._save_pattern,
            3: self._save_circles if self.cfg['pattern']=='circles' else self._save_serp_region,
            4: self._save_circle_timing if self.cfg['pattern']=='circles' else self._save_serp_lines,
            5: self._save_z if self.cfg['pattern']=='circles' else self._save_serp_speed,
            6: self._generate,
        }
        ok = handlers[self.current_step]()
        if ok:
            if self.current_step == self._total_steps():
                self._generate()
            else:
                self.current_step += 1
                self.show_step()

    def prev_step(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.show_step()

    # ── helpers ───────────────────────────────────────────────────────────
    def _title(self, text):
        ctk.CTkLabel(self.view_frame, text=text,
                     font=("Arial", 17, "bold")).pack(pady=(20,10))

    def _row(self, label, widget_fn, default, **kw):
        fr = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        fr.pack(pady=7, fill="x", padx=40)
        ctk.CTkLabel(fr, text=label, width=190, anchor="w").pack(side="left")
        e = widget_fn(fr, **kw)
        if hasattr(e, 'insert'):
            e.insert(0, str(default))
        e.pack(side="right", fill="x", expand=True)
        return e

    def _err(self, text=""):
        lbl = ctk.CTkLabel(self.view_frame, text=text, text_color="#ff6b6b")
        lbl.pack(pady=4)
        return lbl

    def _float(self, fr, **kw): return ctk.CTkEntry(fr, **kw)

    # ── STEP 1 — Plate dimensions ─────────────────────────────────────────
    def _step_plate(self):
        self._title("Step 1 — Base Plate Dimensions")
        self._e_pw = self._row("Plate Width X (mm):",  self._float, self.cfg['plate_w'])
        self._e_ph = self._row("Plate Height Y (mm):", self._float, self.cfg['plate_h'])
        self._e_eo = self._row("Edge Offset (0–10 mm):", self._float, self.cfg['edge_offset'])
        self._lbl_e1 = self._err()

    def _save_plate(self):
        try:
            pw = float(self._e_pw.get())
            ph = float(self._e_ph.get())
            eo = float(self._e_eo.get())
            if pw <= 0 or ph <= 0: raise ValueError("dimensions must be > 0")
            if eo < 0 or eo > 10:  raise ValueError("edge offset must be 0–10")
            self.cfg.update({'plate_w': pw, 'plate_h': ph, 'edge_offset': eo,
                             'sub_w': pw, 'sub_h': ph})
            return True
        except Exception as ex:
            self._lbl_e1.configure(text=f"✗  {ex}")
            return False

    # ── STEP 2 — Pattern ──────────────────────────────────────────────────
    def _step_pattern(self):
        self._title("Step 2 — Pattern Profile Selection")
        ctk.CTkLabel(self.view_frame,
                     text="Choose the scan/deposition pattern:",
                     anchor="w").pack(padx=40, fill="x")

        self._pat_var = ctk.StringVar(value=self.cfg['pattern'])
        for key, label in PAT_LABELS.items():
            ctk.CTkRadioButton(self.view_frame, text=label,
                               variable=self._pat_var, value=key
                               ).pack(anchor="w", padx=60, pady=5)
        self._lbl_e2 = self._err()

    def _save_pattern(self):
        self.cfg['pattern'] = self._pat_var.get()
        return True

    # ── STEP 3a — Circles config ──────────────────────────────────────────
    def _step_circles(self):
        self._title("Step 3 — Circle Array Configuration")
        self._e_cgap  = self._row("Inter-circle gap (mm):",  self._float, self.cfg['circle_gap'])
        self._e_cdiam = self._row("Circle diameter (mm):",   self._float, self.cfg['circle_diameter'])
        self._lbl_capacity = ctk.CTkLabel(self.view_frame, text="", text_color="#aaaaaa")
        self._lbl_capacity.pack(pady=4)
        ctk.CTkButton(self.view_frame, text="Calculate Array Capacity",
                      command=self._calc_array).pack(pady=6)
        self._e_ncirc = self._row("Number of circles:",      self._float, self.cfg['num_circles'])
        self._lbl_e3 = self._err()

    def _calc_array(self):
        try:
            gap  = float(self._e_cgap.get())
            diam = float(self._e_cdiam.get())
            rows, cols, total = calculate_circle_array(
                self.cfg['plate_w'], self.cfg['plate_h'], diam,
                self.cfg['edge_offset'], gap)
            self._lbl_capacity.configure(
                text=f"Array: {rows} rows × {cols} cols = {total} circles max")
        except Exception:
            self._lbl_capacity.configure(text="Enter valid gap and diameter first.")

    def _save_circles(self):
        try:
            gap  = float(self._e_cgap.get())
            diam = float(self._e_cdiam.get())
            nc   = int(float(self._e_ncirc.get()))
            if gap <= 0 or diam <= 0 or nc < 1: raise ValueError
            _, _, total = calculate_circle_array(
                self.cfg['plate_w'], self.cfg['plate_h'], diam,
                self.cfg['edge_offset'], gap)
            if nc > total:
                self._lbl_e3.configure(text=f"✗  Max circles on plate: {total}")
                return False
            self.cfg.update({'circle_gap': gap, 'circle_diameter': diam, 'num_circles': nc})
            return True
        except Exception:
            self._lbl_e3.configure(text="✗  Enter valid positive numbers.")
            return False

    # ── STEP 4a — Circle timing ───────────────────────────────────────────
    def _step_circle_timing(self):
        self._title("Step 4 — Deposition Timing")
        self._e_mtime  = self._row("Time per circle (seconds):",       self._float, self.cfg['motion_time'])
        self._e_stime  = self._row("Step increment per circle (s):",   self._float, self.cfg['step_time'])
        self._e_pause  = self._row("Pause between circles (seconds):", self._float, self.cfg['pause_between'])

        # Show estimated job time live
        self._lbl_jobtime = ctk.CTkLabel(self.view_frame, text="", text_color="#7ec8e3")
        self._lbl_jobtime.pack(pady=6)
        ctk.CTkButton(self.view_frame, text="Estimate Job Time",
                      command=self._est_circle_time).pack(pady=4)
        self._lbl_e4 = self._err()

    def _est_circle_time(self):
        try:
            mt = float(self._e_mtime.get())
            st = float(self._e_stime.get())
            pt = int(float(self._e_pause.get()))
            nc = self.cfg['num_circles']
            t  = calculate_total_job_time(mt, nc, int(st), pt)
            self._lbl_jobtime.configure(
                text=f"Estimated job time: {t['hours']} h  ({t['minutes']} min)")
        except Exception:
            self._lbl_jobtime.configure(text="Enter valid values first.")

    def _save_circle_timing(self):
        try:
            mt = float(self._e_mtime.get())
            st = float(self._e_stime.get())
            pt = int(float(self._e_pause.get()))
            if mt <= 0 or st < 0 or pt < 0: raise ValueError
            # Validate speed
            path_len = calculate_spiral_path_length(self.cfg['circle_diameter'])
            speed = path_len / mt
            if speed < ANYCUBIC_MIN_SPEED or speed > ANYCUBIC_MAX_SPEED:
                self._lbl_e4.configure(
                    text=f"✗  Speed {speed:.1f} mm/s out of range ({ANYCUBIC_MIN_SPEED}–{ANYCUBIC_MAX_SPEED} mm/s)")
                return False
            feedrate = speed * 60
            self.cfg.update({'motion_time': mt, 'step_time': st, 'pause_between': pt,
                             'feedrate': feedrate, 'speed_mms': speed})
            return True
        except Exception:
            self._lbl_e4.configure(text="✗  Enter valid numbers.")
            return False

    # ── STEP 3b — Serpentine region ───────────────────────────────────────
    def _step_serp_region(self):
        self._title("Step 3 — Scan Region")
        ctk.CTkLabel(self.view_frame,
                     text="Scan the entire plate or a centered sub-region?",
                     anchor="w").pack(padx=40, fill="x")

        self._scan_full_var = ctk.IntVar(value=1 if self.cfg['scan_full'] else 0)
        self._chk_full = ctk.CTkCheckBox(self.view_frame, text="Scan entire plate",
                                          variable=self._scan_full_var,
                                          command=self._toggle_subregion)
        self._chk_full.pack(anchor="w", padx=60, pady=10)

        self._sub_frame = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        self._e_sw = self._row_in(self._sub_frame, "Sub-region Width X (mm):",  self.cfg['sub_w'])
        self._e_sh = self._row_in(self._sub_frame, "Sub-region Height Y (mm):", self.cfg['sub_h'])

        self._toggle_subregion()
        self._lbl_e3b = self._err()

    def _row_in(self, parent, label, default):
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(pady=5, fill="x")
        ctk.CTkLabel(fr, text=label, width=220, anchor="w").pack(side="left")
        e = ctk.CTkEntry(fr)
        e.insert(0, str(default))
        e.pack(side="right", fill="x", expand=True)
        return e

    def _toggle_subregion(self):
        if self._scan_full_var.get() == 1:
            self._sub_frame.pack_forget()
        else:
            self._sub_frame.pack(pady=5, fill="x", padx=40)

    def _save_serp_region(self):
        try:
            if self._scan_full_var.get() == 1:
                sw = self.cfg['plate_w'] - 2*self.cfg['edge_offset']
                sh = self.cfg['plate_h'] - 2*self.cfg['edge_offset']
                self.cfg.update({'scan_full': True, 'sub_w': sw, 'sub_h': sh})
            else:
                sw = float(self._e_sw.get())
                sh = float(self._e_sh.get())
                max_w = self.cfg['plate_w'] - 2*self.cfg['edge_offset']
                max_h = self.cfg['plate_h'] - 2*self.cfg['edge_offset']
                if sw <= 0 or sh <= 0 or sw > max_w or sh > max_h:
                    self._lbl_e3b.configure(
                        text=f"✗  Sub-region must be ≤ {max_w:.1f} × {max_h:.1f} mm")
                    return False
                self.cfg.update({'scan_full': False, 'sub_w': sw, 'sub_h': sh})
            return True
        except Exception:
            self._lbl_e3b.configure(text="✗  Enter valid dimensions.")
            return False

    # ── STEP 4b — Serpentine lines ────────────────────────────────────────
    def _step_serp_lines(self):
        self._title("Step 4 — Track Spacing & Line Count")
        self._e_step = self._row("Step-over / line gap (mm):", self._float, self.cfg['step_over'])
        ctk.CTkButton(self.view_frame, text="Calculate Max Lines",
                      command=self._calc_max_lines).pack(pady=6)
        self._lbl_lines_info = ctk.CTkLabel(self.view_frame, text="", text_color="#7ec8e3")
        self._lbl_lines_info.pack(pady=4)
        nl_default = "" if self.cfg['num_lines'] is None else str(self.cfg['num_lines'])
        self._e_nlines = self._row("Line count (blank = all):", self._float, nl_default)
        self._lbl_e4b = self._err()

    def _calc_max_lines(self):
        try:
            step = float(self._e_step.get())
            p = self.cfg['pattern']
            if p == 'serpentine_x':
                ml = max(1, int(self.cfg['sub_h'] / step) + 1)
            else:
                ml = max(1, int(self.cfg['sub_w'] / step) + 1)
            self._max_lines = ml
            self._lbl_lines_info.configure(
                text=f"Max lines that fit: {ml}  "
                     f"(region {self.cfg['sub_w']:.1f}×{self.cfg['sub_h']:.1f} mm, gap {step} mm)")
        except Exception:
            self._lbl_lines_info.configure(text="Enter a valid step-over first.")

    def _save_serp_lines(self):
        try:
            step = float(self._e_step.get())
            if step <= 0: raise ValueError
            # compute max if not done
            p = self.cfg['pattern']
            if p == 'serpentine_x':
                ml = max(1, int(self.cfg['sub_h'] / step) + 1)
            else:
                ml = max(1, int(self.cfg['sub_w'] / step) + 1)
            self._max_lines = ml

            raw = self._e_nlines.get().strip()
            if raw == "":
                nl = ml
            else:
                nl = int(raw)
                if nl < 1 or nl > ml:
                    self._lbl_e4b.configure(text=f"✗  Line count must be 1–{ml}")
                    return False
            self.cfg.update({'step_over': step, 'num_lines': nl})
            return True
        except Exception:
            self._lbl_e4b.configure(text="✗  Enter valid numbers.")
            return False

    # ── STEP 5b — Serpentine speed ────────────────────────────────────────
    def _step_serp_speed(self):
        self._title("Step 5 — Z Depth & Travel Speed")

        # Z depth step selector
        fr_zstep = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        fr_zstep.pack(pady=(8,2), fill="x", padx=40)
        ctk.CTkLabel(fr_zstep, text="Z Step Size:", width=190, anchor="w").pack(side="left")
        self._z_step_var = ctk.StringVar(value="0.2")
        ctk.CTkRadioButton(fr_zstep, text="0.2 mm (default)",
                           variable=self._z_step_var, value="0.2",
                           command=self._rebuild_z_drop).pack(side="left", padx=(0,16))
        ctk.CTkRadioButton(fr_zstep, text="0.1 mm (finer)",
                           variable=self._z_step_var, value="0.1",
                           command=self._rebuild_z_drop).pack(side="left")

        fr_z = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        fr_z.pack(pady=(2,8), fill="x", padx=40)
        ctk.CTkLabel(fr_z, text="Z-Depth (mm):", width=190, anchor="w").pack(side="left")
        self._drop_z = ctk.CTkOptionMenu(fr_z, values=self._z_opts(0.2))
        self._drop_z.set(str(self.cfg['z_down']))
        self._drop_z.pack(side="right", fill="x", expand=True)

        # Speed reference box
        ref_text = (
            "Speed reference  (max 200 mm/s = 12000 mm/min)\n"
            "  🟢 ≤ 20 mm/s  (1200)   — SLOW / electrochemistry safe\n"
            "  🟡 ≤ 60 mm/s  (3600)   — MEDIUM / balanced\n"
            "  🟠 ≤100 mm/s  (6000)   — FAST / check machine\n"
            "  🔴 ≤150 mm/s  (9000)   — VERY FAST / risky\n"
            "  ⛔ ≤200 mm/s  (12000)  — EXTREME / hard limit"
        )
        box = ctk.CTkTextbox(self.view_frame, height=120, width=480,
                              font=("Courier New", 11))
        box.pack(pady=6, padx=20)
        box.insert("1.0", ref_text)
        box.configure(state="disabled")

        self._e_feed = self._row("Feedrate (mm/min):", self._float, int(self.cfg['feedrate']))
        self._lbl_speed_hint = ctk.CTkLabel(self.view_frame, text="", text_color="#7ec8e3")
        self._lbl_speed_hint.pack(pady=2)
        ctk.CTkButton(self.view_frame, text="Check Speed",
                      command=self._check_speed).pack(pady=4)
        self._lbl_e5b = self._err()

    def _check_speed(self):
        try:
            fr = float(self._e_feed.get())
            mms = fr / 60
            lbl = speed_label(mms)
            self._lbl_speed_hint.configure(
                text=f"→ {fr:.0f} mm/min = {mms:.1f} mm/s   {lbl}")
        except Exception:
            self._lbl_speed_hint.configure(text="Enter a valid feedrate first.")

    def _save_serp_speed(self):
        try:
            fr  = float(self._e_feed.get())
            mms = fr / 60
            if fr <= 0:
                self._lbl_e5b.configure(text="✗  Feedrate must be > 0")
                return False
            if mms > ANYCUBIC_MAX_SPEED:
                self._lbl_e5b.configure(
                    text=f"✗  {mms:.1f} mm/s exceeds hard limit of {ANYCUBIC_MAX_SPEED} mm/s")
                return False
            z = float(self._drop_z.get())
            path_len  = calculate_serpentine_path_length(
                self.cfg['sub_w'], self.cfg['sub_h'], self.cfg['step_over'], self.cfg['pattern'])
            motion_t  = path_len / mms if mms > 0 else 0
            self.cfg.update({'feedrate': fr, 'speed_mms': mms,
                             'z_down': z, 'motion_time': motion_t})
            return True
        except Exception:
            self._lbl_e5b.configure(text="✗  Invalid values.")
            return False

    # ── STEP 5a — Z depth for circles ────────────────────────────────────
    def _step_z(self):
        self._title("Step 5 — Z Axis Working Depth")
        ctk.CTkLabel(self.view_frame,
                     text="Range: -11.0 mm  to  -13.0 mm",
                     text_color="#aaaaaa").pack(pady=(0,6))

        fr_zstep = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        fr_zstep.pack(pady=(4,2), fill="x", padx=40)
        ctk.CTkLabel(fr_zstep, text="Z Step Size:", width=190, anchor="w").pack(side="left")
        self._z_step_var = ctk.StringVar(value="0.2")
        ctk.CTkRadioButton(fr_zstep, text="0.2 mm (default)",
                           variable=self._z_step_var, value="0.2",
                           command=self._rebuild_z_drop_c).pack(side="left", padx=(0,16))
        ctk.CTkRadioButton(fr_zstep, text="0.1 mm (finer)",
                           variable=self._z_step_var, value="0.1",
                           command=self._rebuild_z_drop_c).pack(side="left")

        fr_z = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        fr_z.pack(pady=(2,8), fill="x", padx=40)
        ctk.CTkLabel(fr_z, text="Z-Depth (mm):", width=190, anchor="w").pack(side="left")
        self._drop_z_c = ctk.CTkOptionMenu(fr_z, values=self._z_opts(0.2))
        self._drop_z_c.set(str(self.cfg['z_down']))
        self._drop_z_c.pack(side="right", fill="x", expand=True)
        self._lbl_e5c = self._err()

    def _save_z(self):
        try:
            self.cfg['z_down'] = float(self._drop_z_c.get())
            return True
        except Exception:
            self._lbl_e5c.configure(text="✗  Select a Z depth.")
            return False

    # ── STEP 6 — Summary (circles only) ───────────────────────────────────
    def _step_summary(self):
        self._title("Step 6 — Verify & Generate")
        c = self.cfg
        timing = calculate_total_job_time(
            c['motion_time'], c['num_circles'], int(c['step_time']), c['pause_between'])
        _, _, total = calculate_circle_array(
            c['plate_w'], c['plate_h'], c['circle_diameter'], c['edge_offset'], c['circle_gap'])

        summary = (
            f" ═══════════════════════════════════════════\n"
            f"   GCODE MANIFEST — CIRCLES\n"
            f" ═══════════════════════════════════════════\n"
            f"  Plate          : {c['plate_w']} × {c['plate_h']} mm\n"
            f"  Edge offset    : {c['edge_offset']} mm\n"
            f"  Circle Ø       : {c['circle_diameter']} mm\n"
            f"  Circle gap     : {c['circle_gap']} mm\n"
            f"  Circles        : {c['num_circles']} of {total} max\n"
            f"  Time / circle  : {c['motion_time']} s  (+{c['step_time']} s step)\n"
            f"  Pause between  : {c['pause_between']} s\n"
            f"  Z-depth        : {c['z_down']:.1f} mm\n"
            f"  Speed          : {c['speed_mms']:.2f} mm/s  (F{c['feedrate']:.1f})\n"
            f"  {speed_label(c['speed_mms'])}\n"
            f" ───────────────────────────────────────────\n"
            f"  Est. job time  : {timing['hours']} h  ({timing['minutes']} min)\n"
            f" ═══════════════════════════════════════════\n"
        )
        box = ctk.CTkTextbox(self.view_frame, height=320, width=490,
                              font=("Courier New", 11))
        box.pack(pady=10, padx=20)
        box.insert("1.0", summary)
        box.configure(state="disabled")

    # ── Z depth helpers ──────────────────────────────────────────────────────
    def _z_opts(self, step):
        """Build dropdown list from -11.0 to -13.0 with given step (0.1 or 0.2)"""
        step = float(step)
        n = round(2.0 / step) + 1  # -11.0 to -13.0 = 2.0 mm span
        return [str(round(-11.0 - i * step, 2)) for i in range(n)]

    def _rebuild_z_drop(self):
        """Serpentine speed step: rebuild dropdown when step radio changes"""
        step = self._z_step_var.get()
        opts = self._z_opts(step)
        self._drop_z.configure(values=opts)
        self._drop_z.set(opts[0])  # reset to -11.0

    def _rebuild_z_drop_c(self):
        """Circles step: rebuild dropdown when step radio changes"""
        step = self._z_step_var.get()
        opts = self._z_opts(step)
        self._drop_z_c.configure(values=opts)
        self._drop_z_c.set(opts[0])  # reset to -11.0

    # ── GENERATE ──────────────────────────────────────────────────────────
    def _generate(self):
        try:
            OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
            gcode_text = build_gcode(self.cfg)
            move_cnt   = sum(1 for l in gcode_text.split("\n")
                             if l.startswith(("G0","G1")))
            ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            pat = self.cfg['pattern']
            out = OUTPUT_FOLDER / f"gcode_{pat}_{ts}.gcode"
            out.write_text(gcode_text, encoding="utf-8")

            pop = ctk.CTkToplevel(self)
            pop.title("✦ Export Complete")
            pop.geometry("460x220")
            pop.transient(self); pop.grab_set()

            ctk.CTkLabel(pop, text="✦  GCODE EXPORT COMPLETE",
                         font=("Arial", 14, "bold"), text_color="#5bc85b").pack(pady=18)
            ctk.CTkLabel(pop,
                         text=f"Folder:  {OUTPUT_FOLDER.resolve()}\n"
                              f"File:    {out.name}\n"
                              f"Moves:   {move_cnt} G0/G1 blocks",
                         justify="center", font=("Arial", 11)).pack(pady=6)

            def reset():
                pop.destroy()
                self.current_step = 1
                self.show_step()

            ctk.CTkButton(pop, text="Done — Start New", command=reset).pack(pady=14)

        except Exception as ex:
            ep = ctk.CTkToplevel(self)
            ep.title("Error")
            ep.geometry("340x130")
            ctk.CTkLabel(ep, text=f"Export failed:\n{ex}", text_color="red").pack(pady=20)

        return True


if __name__ == "__main__":
    app = GCodeWizardApp()
    app.mainloop()
