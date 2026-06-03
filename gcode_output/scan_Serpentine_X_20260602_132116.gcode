; ============================================================
; Electrochemistry Scan — Serpentine X
; Date/Time    : 2026-06-02 13:21:16
; Plate        : 100.0 x 100.0 mm (centered)
; Edge offset  : 2.0 mm (outside plate boundary)
; Sub-region   : 100.0 x 100.0 mm (centered on plate)
; Gap          : 4.0 mm  |  Lines: 26
; Z-down       : -11.0 mm
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
G0 Z-11.0
G1 X52.0 Y-52.0
G1 X52.0 Y52.0
G1 X-52.0 Y52.0
G1 X-52.0 Y-52.0
G0 Z0

; --- SECOND SKIRTING LOOP (inner) ---
G0 X-51.0 Y-51.0
G0 Z-11.0
G1 X51.0 Y-51.0
G1 X51.0 Y51.0
G1 X-51.0 Y51.0
G1 X-51.0 Y-51.0
G0 Z0

G4 P90000  ; PAUSE FOR ADJUSTMENTS

; --- SCAN LINES: SERPENTINE X ---
G0 X-50.0 Y-50.0
G1 X50.0 Y-50.0 Z-11.0
G0 X50.0 Y-46.0
G1 X-50.0 Y-46.0 Z-11.0
G0 X-50.0 Y-42.0
G1 X50.0 Y-42.0 Z-11.0
G0 X50.0 Y-38.0
G1 X-50.0 Y-38.0 Z-11.0
G0 X-50.0 Y-34.0
G1 X50.0 Y-34.0 Z-11.0
G0 X50.0 Y-30.0
G1 X-50.0 Y-30.0 Z-11.0
G0 X-50.0 Y-26.0
G1 X50.0 Y-26.0 Z-11.0
G0 X50.0 Y-22.0
G1 X-50.0 Y-22.0 Z-11.0
G0 X-50.0 Y-18.0
G1 X50.0 Y-18.0 Z-11.0
G0 X50.0 Y-14.0
G1 X-50.0 Y-14.0 Z-11.0
G0 X-50.0 Y-10.0
G1 X50.0 Y-10.0 Z-11.0
G0 X50.0 Y-6.0
G1 X-50.0 Y-6.0 Z-11.0
G0 X-50.0 Y-2.0
G1 X50.0 Y-2.0 Z-11.0
G0 X50.0 Y2.0
G1 X-50.0 Y2.0 Z-11.0
G0 X-50.0 Y6.0
G1 X50.0 Y6.0 Z-11.0
G0 X50.0 Y10.0
G1 X-50.0 Y10.0 Z-11.0
G0 X-50.0 Y14.0
G1 X50.0 Y14.0 Z-11.0
G0 X50.0 Y18.0
G1 X-50.0 Y18.0 Z-11.0
G0 X-50.0 Y22.0
G1 X50.0 Y22.0 Z-11.0
G0 X50.0 Y26.0
G1 X-50.0 Y26.0 Z-11.0
G0 X-50.0 Y30.0
G1 X50.0 Y30.0 Z-11.0
G0 X50.0 Y34.0
G1 X-50.0 Y34.0 Z-11.0
G0 X-50.0 Y38.0
G1 X50.0 Y38.0 Z-11.0
G0 X50.0 Y42.0
G1 X-50.0 Y42.0 Z-11.0
G0 X-50.0 Y46.0
G1 X50.0 Y46.0 Z-11.0
G0 X50.0 Y50.0
G1 X-50.0 Y50.0 Z-11.0

G0 Z0 ; Safe height
G0 X0 Y0 ; Return origin
M84 S0 ; Disable motors