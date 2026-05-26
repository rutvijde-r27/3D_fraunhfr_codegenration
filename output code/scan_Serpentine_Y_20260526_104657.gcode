; ═══════════════════════════════════════════════════
; GCode — Plate Scanning
; Machine    : Anycubic Mega X
; Pattern    : Serpentine Y
; Plate      : 100.0 × 100.0 mm
; Edge offset: 20.0 mm
; Scan area  : X20.0+5.0  Y20.0+20.0 mm
; Gap        : 1.0 mm  |  Lines: 4
; Speed      : 65.0 mm/s  (3900.0 mm/min)
; Skirting   : No
; Generated  : 2026-05-26 10:46:57
; ═══════════════════════════════════════════════════
G90          ; Absolute positioning
G21          ; Units: mm
F3900.0  ; Feedrate
G0 X0 Y0     ; Home to origin

; ─── Serpentine Y (lines along Y, stepping in X) ───
G0 X20.0 Y20.0  ; line 1 start
G1 X20.0 Y40.0  ; line 1 end
G0 X21.0 Y40.0  ; line 2 start
G1 X21.0 Y20.0  ; line 2 end
G0 X22.0 Y20.0  ; line 3 start
G1 X22.0 Y40.0  ; line 3 end
G0 X23.0 Y40.0  ; line 4 start
G1 X23.0 Y20.0  ; line 4 end

G0 X0 Y0     ; Return to origin
M30          ; End program