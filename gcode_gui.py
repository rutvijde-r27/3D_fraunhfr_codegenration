#!/usr/bin/env python3
import customtkinter as ctk
import math
from pathlib import Path
from datetime import datetime

# ==============================================================================
#  MACHINE CONSTANTS
# ==============================================================================
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

# ==============================================================================
#  GEOMETRY CORE ENGINE
# ==============================================================================
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

# ==============================================================================
#  GCODE BUILD STRING GENERATORS
# ==============================================================================
def gc_header(cfg):
    pat_names = {1:"Serpentine X", 2:"Serpentine Y", 3:f"Diagonal {cfg['angle']}°"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "; ============================================================",
        f"; Electrochemistry Scan — {pat_names[cfg['pattern']]}",
        f"; Date/Time    : {now}",
        f"; Plate        : {cfg['plate_w']} x {cfg['plate_h']} mm (centered)",
        f"; Edge offset  : {cfg['edge_offset']} mm (outside plate boundary)",
        f"; Sub-region   : {cfg['sub_w']} x {cfg['sub_h']} mm (centered on plate)",
        f"; Gap          : {cfg['gap']} mm  |  Lines: {cfg['n_lines']}",
        f"; Z-down       : {cfg['z_down']:.1f} mm",
        f"; Speed        : {cfg['speed_mms']:.1f} mm/s  (F{cfg['feedrate']:.0f})",
        f"; Skirting     : {SKIRT_PASSES} pass(es), {SKIRT_DWELL_S}s pause",
        "; ============================================================",
        "",
        "; Coordinate system: Centered on plate (logical coords)",
        f"; Physical origin (after homeZ12): X={LOGICAL_ORIGIN_X} Y={LOGICAL_ORIGIN_Y} Z={LOGICAL_ORIGIN_Z}",
        "",
        "G21  ; mm units",
        "G90  ; absolute coordinates",
        f"F{cfg['feedrate']:.0f}  ; feedrate",
        "",
    ]

def gc_skirt(plate_w, plate_h, edge_offset, z_down):
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
    
    return [
        "; --- FIRST SKIRTING LOOP (outer) ---",
        f"G0 X{x0_skirt1} Y{y0_skirt1}",
        f"G0 Z{z_down:.1f}",
        f"G1 X{x1_skirt1} Y{y0_skirt1}",
        f"G1 X{x1_skirt1} Y{y1_skirt1}",
        f"G1 X{x0_skirt1} Y{y1_skirt1}",
        f"G1 X{x0_skirt1} Y{y0_skirt1}",
        "G0 Z0",
        "",
        "; --- SECOND SKIRTING LOOP (inner) ---",
        f"G0 X{x0_skirt2} Y{y0_skirt2}",
        f"G0 Z{z_down:.1f}",
        f"G1 X{x1_skirt2} Y{y0_skirt2}",
        f"G1 X{x1_skirt2} Y{y1_skirt2}",
        f"G1 X{x0_skirt2} Y{y1_skirt2}",
        f"G1 X{x0_skirt2} Y{y0_skirt2}",
        "G0 Z0",
        "",
        f"G4 P{SKIRT_DWELL_S * 1000}  ; PAUSE FOR ADJUSTMENTS",
    ]

def gc_scan_serpentine_x(sub_ox, sub_oy, sub_w, sub_h, gap, n, z_down):
    lines = ["; --- SCAN LINES: SERPENTINE X ---"]
    for i in range(n):
        y = f(sub_oy + i * gap)
        if y > sub_oy + sub_h: break
        xs = f(sub_ox) if i % 2 == 0 else f(sub_ox + sub_w)
        xe = f(sub_ox + sub_w) if i % 2 == 0 else f(sub_ox)
        lines += [
            f"G0 X{xs} Y{y}",
            f"G1 X{xe} Y{y} Z{z_down:.1f}",
        ]
    return lines

def gc_scan_serpentine_y(sub_ox, sub_oy, sub_w, sub_h, gap, n, z_down):
    lines = ["; --- SCAN LINES: SERPENTINE Y ---"]
    for i in range(n):
        x = f(sub_ox + i * gap)
        if x > sub_ox + sub_w: break
        ys = f(sub_oy) if i % 2 == 0 else f(sub_oy + sub_h)
        ye = f(sub_oy + sub_h) if i % 2 == 0 else f(sub_oy)
        lines += [
            f"G0 X{x} Y{ys}",
            f"G1 X{x} Y{ye} Z{z_down:.1f}",
        ]
    return lines

def gc_scan_diagonal(sub_ox, sub_oy, sub_w, sub_h, gap, n, angle_deg, z_down):
    lines = [f"; --- SCAN LINES: DIAGONAL {angle_deg} DEG ---"]
    ar = math.radians(angle_deg)
    ca, sa = math.cos(ar), math.sin(ar)
    hl = math.hypot(sub_w, sub_h) * 1.5
    
    for i in range(n):
        mx = sub_ox + sub_w/2 + i * gap * (-sa)
        my = sub_oy + sub_h/2 + i * gap * ca
        p1, p2 = clip_line(mx - hl*ca, my - hl*sa, mx + hl*ca, my + hl*sa,
                            sub_ox, sub_ox + sub_w, sub_oy, sub_oy + sub_h)
        if p1 is None or p2 is None: continue
        x1, y1 = f(p1[0]), f(p1[1])
        x2, y2 = f(p2[0]), f(p2[1])
        if i % 2 == 1: x1, y1, x2, y2 = x2, y2, x1, y1
        lines += [
            f"G0 X{x1} Y{y1}",
            f"G1 X{x2} Y{y2} Z{z_down:.1f}",
        ]
    return lines

def gc_footer():
    return ["", "G0 Z0 ; Safe height", "G0 X0 Y0 ; Return origin", "M84 S0 ; Disable motors"]

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

# ==============================================================================
#  WIZARD INTERFACE CONTROLLER
# ==============================================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GCodeWizardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Anycubic Mega X Setup Wizard")
        self.geometry("560x660")
        self.resizable(False, False)

        # Base active application configuration dictionary
        self.cfg = {
            'plate_w': 100.0,
            'plate_h': 100.0,
            'edge_offset': 2.0,
            'pattern': 1,
            'angle': 45.0,
            'scan_full': True,
            'sub_w': 100.0,
            'sub_h': 100.0,
            'gap': 4.0,
            'n_lines': 26,
            'z_down': -11.0,
            'feedrate': 2400.0,
            'speed_mms': 40.0,
            'sub_ox': -50.0,
            'sub_oy': -50.0
        }
        self.current_step = 1
        self.max_lines_computed = 26

        self.view_container = ctk.CTkFrame(self, corner_radius=12)
        self.view_container.pack(padx=25, pady=25, fill="both", expand=True)

        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=25, pady=(0, 20))

        self.btn_back = ctk.CTkButton(self.nav_frame, text="Back", command=self.prev_step, state="disabled", width=110)
        self.btn_back.pack(side="left")

        self.step_indicator = ctk.CTkLabel(self.nav_frame, text="Step 1 of 5", font=("Arial", 13, "bold"))
        self.step_indicator.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(self.nav_frame, text="Next", command=self.next_step, width=110)
        self.btn_next.pack(side="right")

        self.show_step()

    def clear_view(self):
        for widget in self.view_container.winfo_children():
            widget.destroy()

    def show_step(self):
        self.clear_view()
        self.step_indicator.configure(text=f"Step {self.current_step} of 5")
        self.btn_back.configure(state="normal" if self.current_step > 1 else "disabled")
        self.btn_next.configure(text="Generate File" if self.current_step == 5 else "Next")

        if self.current_step == 1: self.render_step_1()
        elif self.current_step == 2: self.render_step_2()
        elif self.current_step == 3: self.render_step_3()
        elif self.current_step == 4: self.render_step_4()
        elif self.current_step == 5: self.render_step_5()

    def render_step_1(self):
        ctk.CTkLabel(self.view_container, text="Base Plate Dimensions", font=("Arial", 18, "bold")).pack(pady=20)
        
        f1 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f1.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f1, text="Plate Width (mm):", width=150, anchor="w").pack(side="left")
        self.entry_pw = ctk.CTkEntry(f1)
        self.entry_pw.insert(0, str(self.cfg['plate_w']))
        self.entry_pw.pack(side="right", fill="x", expand=True)

        f2 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f2.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f2, text="Plate Height (mm):", width=150, anchor="w").pack(side="left")
        self.entry_ph = ctk.CTkEntry(f2)
        self.entry_ph.insert(0, str(self.cfg['plate_h']))
        self.entry_ph.pack(side="right", fill="x", expand=True)

        f3 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f3.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f3, text="Edge Offset (mm):", width=150, anchor="w").pack(side="left")
        self.entry_eo = ctk.CTkEntry(f3)
        self.entry_eo.insert(0, str(self.cfg['edge_offset']))
        self.entry_eo.pack(side="right", fill="x", expand=True)

        self.lbl_err1 = ctk.CTkLabel(self.view_container, text="", text_color="red")
        self.lbl_err1.pack(pady=15)

    def render_step_2(self):
        ctk.CTkLabel(self.view_container, text="Scan Target Setup", font=("Arial", 18, "bold")).pack(pady=20)

        f1 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f1.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f1, text="Scan Style:", width=150, anchor="w").pack(side="left")
        
        self.opt_pat = ctk.CTkOptionMenu(f1, values=["Serpentine X", "Serpentine Y", "Diagonal"], command=self.toggle_diagonal)
        p_idx = self.cfg['pattern']
        self.opt_pat.set(["Serpentine X", "Serpentine Y", "Diagonal"][p_idx-1])
        self.opt_pat.pack(side="right", fill="x", expand=True)

        self.f_diag = ctk.CTkFrame(self.view_container, fg_color="transparent")
        ctk.CTkLabel(self.f_diag, text="Angle (0-179°):", width=150, anchor="w").pack(side="left")
        self.entry_angle = ctk.CTkEntry(self.f_diag)
        self.entry_angle.insert(0, str(self.cfg['angle']))
        self.entry_angle.pack(side="right", fill="x", expand=True)

        f2 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f2.pack(pady=15, fill="x", padx=40)
        self.check_full = ctk.CTkCheckBox(f2, text="Scan Entire Plate Area", command=self.toggle_subregion)
        if self.cfg['scan_full']: self.check_full.select()
        self.check_full.pack(anchor="w")

        self.f_sub = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f_w = ctk.CTkFrame(self.f_sub, fg_color="transparent")
        f_w.pack(pady=5, fill="x")
        ctk.CTkLabel(f_w, text="Sub Width (mm):", width=150, anchor="w").pack(side="left")
        self.entry_sw = ctk.CTkEntry(f_w)
        self.entry_sw.insert(0, str(self.cfg['sub_w']))
        self.entry_sw.pack(side="right", fill="x", expand=True)

        f_h = ctk.CTkFrame(self.f_sub, fg_color="transparent")
        f_h.pack(pady=5, fill="x")
        ctk.CTkLabel(f_h, text="Sub Height (mm):", width=150, anchor="w").pack(side="left")
        self.entry_sh = ctk.CTkEntry(f_h)
        self.entry_sh.insert(0, str(self.cfg['sub_h']))
        self.entry_sh.pack(side="right", fill="x", expand=True)
        
        self.toggle_diagonal(self.opt_pat.get())
        self.toggle_subregion()

        self.lbl_err2 = ctk.CTkLabel(self.view_container, text="", text_color="red")
        self.lbl_err2.pack(pady=10)

    def toggle_diagonal(self, val):
        if val == "Diagonal": self.f_diag.pack(pady=10, fill="x", padx=40, before=self.check_full.master)
        else: self.f_diag.pack_forget()

    def toggle_subregion(self):
        if self.check_full.get() == 0: self.f_sub.pack(pady=10, fill="x", padx=40)
        else: self.f_sub.pack_forget()

    def render_step_3(self):
        ctk.CTkLabel(self.view_container, text="Spacing & Line Density", font=("Arial", 18, "bold")).pack(pady=20)

        f1 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f1.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f1, text="Line Gap (mm):", width=150, anchor="w").pack(side="left")
        self.entry_gap = ctk.CTkEntry(f1)
        self.entry_gap.insert(0, str(self.cfg['gap']))
        self.entry_gap.pack(side="right", fill="x", expand=True)

        ctk.CTkButton(self.view_container, text="Recalculate Bounds", command=self.calc_lines_gui).pack(pady=10)

        self.box_info = ctk.CTkTextbox(self.view_container, height=120, width=420)
        self.box_info.pack(pady=10)

        f2 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f2.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f2, text="Line Count to Run:", width=150, anchor="w").pack(side="left")
        self.entry_lines = ctk.CTkEntry(f2, placeholder_text="Leave blank to use maximum")
        self.entry_lines.insert(0, str(self.cfg['n_lines']))
        self.entry_lines.pack(side="right", fill="x", expand=True)

        self.lbl_err3 = ctk.CTkLabel(self.view_container, text="", text_color="red")
        self.lbl_err3.pack(pady=5)
        self.calc_lines_gui()

    def calc_lines_gui(self):
        try:
            gap = float(self.entry_gap.get())
            ml = max_lines_possible(self.cfg['sub_w'], self.cfg['sub_h'], self.cfg['pattern'], gap, self.cfg['angle'])
            if not gap_fits(self.cfg['sub_w'], self.cfg['sub_h'], self.cfg['pattern'], gap, self.cfg['angle']):
                self.box_info.delete("1.0", "end")
                self.box_info.insert("1.0", "X Spacing pitch exceeds envelope frame limits bounds.")
                return False
            self.box_info.delete("1.0", "end")
            self.box_info.insert("1.0", f" - Geometry Area Bounds : {self.cfg['sub_w']} x {self.cfg['sub_h']} mm\n"
                                        f" - Structural Gap Step  : {gap} mm\n"
                                        f" - Maximum Lines Fitting: {ml} tracks")
            self.max_lines_computed = ml
            return True
        except ValueError: return False

    def render_step_4(self):
        ctk.CTkLabel(self.view_container, text="Tool Depth & Velocity Profiles", font=("Arial", 18, "bold")).pack(pady=20)

        f1 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f1.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f1, text="Z-Depth Profile Axis:", width=150, anchor="w").pack(side="left")
        z_options = [str(round(-9.0 - (x * 0.2), 1)) for x in range(21)]
        self.drop_z = ctk.CTkOptionMenu(f1, values=z_options)
        self.drop_z.set(str(self.cfg['z_down']))
        self.drop_z.pack(side="right", fill="x", expand=True)

        f2 = ctk.CTkFrame(self.view_container, fg_color="transparent")
        f2.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(f2, text="Feedrate Speed (mm/min):", width=180, anchor="w").pack(side="left")
        self.entry_feed = ctk.CTkEntry(f2)
        self.entry_feed.insert(0, str(self.cfg['feedrate']))
        self.entry_feed.pack(side="right", fill="x", expand=True)

        self.lbl_err4 = ctk.CTkLabel(self.view_container, text="", text_color="red")
        self.lbl_err4.pack(pady=15)

    def render_step_5(self):
        ctk.CTkLabel(self.view_container, text="Execute System Sequence Verification", font=("Arial", 18, "bold")).pack(pady=15)
        self.txt_summary = ctk.CTkTextbox(self.view_container, height=360, width=460, font=("Courier New", 12))
        self.txt_summary.pack(pady=10)

        p_name = ["Serpentine X", "Serpentine Y", f"Diagonal {self.cfg['angle']} deg"][self.cfg['pattern'] - 1]
        summary = (
            f" =======================================================\n"
            f"   G-CODE MANIFEST VERIFICATION DETAILS\n"
            f" =======================================================\n"
            f"  - Platform Framework: {self.cfg['plate_w']} x {self.cfg['plate_h']} mm\n"
            f"  - Skirting Bounds   : +{self.cfg['edge_offset']} mm Offset\n"
            f"  - Motion Path Style : {p_name}\n"
            f"  - Target Region Box : {self.cfg['sub_w']} x {self.cfg['sub_h']} mm\n"
            f"  - Track Step Pitch  : {self.cfg['gap']} mm spacing\n"
            f"  - Traversal Density : {self.cfg['n_lines']} line elements\n"
            f"  - Target Z Depth    : {self.cfg['z_down']:.1f} mm\n"
            f"  - Running Velocity  : {self.cfg['feedrate']:.0f} mm/min ({self.cfg['speed_mms']:.1f} mm/s)\n"
            f" =======================================================\n"
        )
        self.txt_summary.insert("1.0", summary)
        self.txt_summary.configure(state="disabled")

    def next_step(self):
        # Read and save UI fields IMMEDIATELY on clicking next to prevent missing keys
        if self.current_step == 1:
            try:
                pw = float(self.entry_pw.get())
                ph = float(self.entry_ph.get())
                eo = float(self.entry_eo.get())
                if pw <= 0 or ph <= 0 or eo < 0 or eo > 10: raise ValueError
                self.cfg['plate_w'], self.cfg['plate_h'], self.cfg['edge_offset'] = pw, ph, eo
            except ValueError:
                self.lbl_err1.configure(text="Verify entry values are positive dimensions.")
                return

        elif self.current_step == 2:
            p_map = {"Serpentine X": 1, "Serpentine Y": 2, "Diagonal": 3}
            self.cfg['pattern'] = p_map[self.opt_pat.get()]
            if self.cfg['pattern'] == 3:
                try:
                    ang = float(self.entry_angle.get())
                    if ang < 0 or ang >= 180: raise ValueError
                    self.cfg['angle'] = ang
                except ValueError:
                    self.lbl_err2.configure(text="Angle scope limit invalid (0-179).")
                    return
            else: self.cfg['angle'] = 45.0

            if self.check_full.get() == 1:
                self.cfg['scan_full'] = True
                self.cfg['sub_w'], self.cfg['sub_h'] = self.cfg['plate_w'], self.cfg['plate_h']
            else:
                self.cfg['scan_full'] = False
                try:
                    sw = float(self.entry_sw.get())
                    sh = float(self.entry_sh.get())
                    if sw <= 0 or sw > self.cfg['plate_w'] or sh <= 0 or sh > self.cfg['plate_h']: raise ValueError
                    self.cfg['sub_w'], self.cfg['sub_h'] = sw, sh
                except ValueError:
                    self.lbl_err2.configure(text="Sub envelope values exceed full base coordinates.")
                    return
            self.cfg['sub_ox'] = -self.cfg['sub_w'] / 2
            self.cfg['sub_oy'] = -self.cfg['sub_h'] / 2

        elif self.current_step == 3:
            try:
                gap = float(self.entry_gap.get())
                self.cfg['gap'] = gap
            except ValueError:
                self.lbl_err3.configure(text="Invalid gap value.")
                return

            if not self.calc_lines_gui(): return
            raw = self.entry_lines.get().strip()
            if raw == "": self.cfg['n_lines'] = self.max_lines_computed
            else:
                try:
                    nl = int(raw)
                    if nl < 1 or nl > self.max_lines_computed: raise ValueError
                    self.cfg['n_lines'] = nl
                except ValueError:
                    self.lbl_err3.configure(text=f"Line range out of limits (1-{self.max_lines_computed}).")
                    return

        elif self.current_step == 4:
            try:
                fr = float(self.entry_feed.get())
                mms = fr / 60.0
                if fr <= 0 or mms > MEGA_X_MAX_MMS: raise ValueError
                self.cfg['feedrate'], self.cfg['speed_mms'] = fr, mms
                self.cfg['z_down'] = float(self.drop_z.get())
            except ValueError:
                self.lbl_err4.configure(text=f"Speed exceeds mechanical velocity boundary limit ({MEGA_X_MAX_MMS * 60} mm/min max).")
                return

        elif self.current_step == 5:
            self.compile_output()
            return

        self.current_step += 1
        self.show_step()

    def prev_step(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.show_step()

    def compile_output(self):
        try:
            OUTPUT_FOLDER.mkdir(exist_ok=True)
            text_block = build_gcode(self.cfg)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            pat_lbl = ["Serpentine_X", "Serpentine_Y", "Diagonal"][self.cfg['pattern'] - 1]
            
            target_path = OUTPUT_FOLDER / f"scan_{pat_lbl}_{ts}.gcode"
            target_path.write_text(text_block, encoding="utf-8")

            pop = ctk.CTkToplevel(self)
            pop.title("Process Success")
            pop.geometry("440x200")
            pop.transient(self)
            pop.grab_set()

            ctk.CTkLabel(pop, text="G-CODE EXPORT FINALIZED", font=("Arial", 14, "bold"), text_color="green").pack(pady=15)
            path_msg = f"Saved in folder:\n{OUTPUT_FOLDER.resolve()}\n\nFile: {target_path.name}"
            ctk.CTkLabel(pop, text=path_msg, justify="center", font=("Arial", 11)).pack(pady=5)

            def reset():
                pop.destroy()
                self.current_step = 1
                self.show_step()
            ctk.CTkButton(pop, text="Done", command=reset).pack(pady=15)
        except Exception as e:
            err_pop = ctk.CTkToplevel(self)
            err_pop.title("Error")
            err_pop.geometry("300x120")
            ctk.CTkLabel(err_pop, text=f"Write Failed:\n{str(e)}", text_color="red").pack(pady=20)

if __name__ == "__main__":
    app = GCodeWizardApp()
    app.mainloop()