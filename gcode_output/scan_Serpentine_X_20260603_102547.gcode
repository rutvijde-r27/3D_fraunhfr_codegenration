; ============================================================
; Electrochemistry Scan — Serpentine X
; Date/Time    : 2026-06-03 10:25:47
; Plate        : 100.0 x 100.0 mm (centered)
; Edge offset  : 2.0 mm (outside plate boundary)
; Sub-region   : 50.0 x 50.0 mm (centered on plate)
; Gap          : 2.0 mm  |  Lines: 24
; Z-down       : -12.8 mm
; Speed        : 40.0 mm/s  (F2400)
; Skirting     : 1 pass(es), 90s pause
; ============================================================

; Coordinate system: Centered on plate (logical coords)
; Physical origin (after homeZ12): X=150 Y=150 Z=120

G21  ; mm units
G90  ; absolute coordinates
F2400  ; feedrate

; --- FIRST SKIRTING LOOP (outer) ---
G0 X-52.0 Y-52.0
G0 Z-12.8
G1 X52.0 Y-52.0
G1 X52.0 Y52.0
G1 X-52.0 Y52.0
G1 X-52.0 Y-52.0
G0 Z0

; --- SECOND SKIRTING LOOP (inner) ---
G0 X-51.0 Y-51.0
G0 Z-12.8
G1 X51.0 Y-51.0
G1 X51.0 Y51.0
G1 X-51.0 Y51.0
G1 X-51.0 Y-51.0
G0 Z0

G4 P90000  ; PAUSE FOR ADJUSTMENTS

; --- SCAN LINES: SERPENTINE X ---
G0 X-25.0 Y-25.0
G1 X25.0 Y-25.0 Z-12.8
G0 X25.0 Y-23.0
G1 X-25.0 Y-23.0 Z-12.8
G0 X-25.0 Y-21.0
G1 X25.0 Y-21.0 Z-12.8
G0 X25.0 Y-19.0
G1 X-25.0 Y-19.0 Z-12.8
G0 X-25.0 Y-17.0
G1 X25.0 Y-17.0 Z-12.8
G0 X25.0 Y-15.0
G1 X-25.0 Y-15.0 Z-12.8
G0 X-25.0 Y-13.0
G1 X25.0 Y-13.0 Z-12.8
G0 X25.0 Y-11.0
G1 X-25.0 Y-11.0 Z-12.8
G0 X-25.0 Y-9.0
G1 X25.0 Y-9.0 Z-12.8
G0 X25.0 Y-7.0
G1 X-25.0 Y-7.0 Z-12.8
G0 X-25.0 Y-5.0
G1 X25.0 Y-5.0 Z-12.8
G0 X25.0 Y-3.0
G1 X-25.0 Y-3.0 Z-12.8
G0 X-25.0 Y-1.0
G1 X25.0 Y-1.0 Z-12.8
G0 X25.0 Y1.0
G1 X-25.0 Y1.0 Z-12.8
G0 X-25.0 Y3.0
G1 X25.0 Y3.0 Z-12.8
G0 X25.0 Y5.0
G1 X-25.0 Y5.0 Z-12.8
G0 X-25.0 Y7.0
G1 X25.0 Y7.0 Z-12.8
G0 X25.0 Y9.0
G1 X-25.0 Y9.0 Z-12.8
G0 X-25.0 Y11.0
G1 X25.0 Y11.0 Z-12.8
G0 X25.0 Y13.0
G1 X-25.0 Y13.0 Z-12.8
G0 X-25.0 Y15.0
G1 X25.0 Y15.0 Z-12.8
G0 X25.0 Y17.0
G1 X-25.0 Y17.0 Z-12.8
G0 X-25.0 Y19.0
G1 X25.0 Y19.0 Z-12.8
G0 X25.0 Y21.0
G1 X-25.0 Y21.0 Z-12.8

G0 Z0 ; Safe height
G0 X0 Y0 ; Return origin
M84 S0 ; Disable motors