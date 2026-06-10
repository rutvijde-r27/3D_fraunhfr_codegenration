; ════════════════════════════════════════════════════════════
; Electrochemistry Scan — Serpentine X
; Date/Time    : 2026-06-08 13:34:04
; Plate        : 100.0 × 100.0 mm (centered)
; Edge offset  : 2.0 mm (outside plate boundary)
; Sub-region   : 50.0 × 50.0 mm (centered on plate)
; Gap          : 2.0 mm  |  Lines: 25
; Z-down       : -12.4 mm
; Speed        : 100.0 mm/s  (F6000.0)
; Skirting     : 1 pass(es), 90s pause
; ════════════════════════════════════════════════════════════

; Coordinate system: Centered on plate (logical coords)
; Physical origin (after homeZ12): X=150 Y=150 Z=120

G21  ; mm units
G90  ; absolute coordinates
F6000.0  ; feedrate

; ════════════════════════════════════════════════════════════
; SKIRTING — 2 consecutive rectangular loops around plate
; Plate boundary      : ±50.0 X, ±50.0 Y
; 1st skirting (outer): ±52.0 X, ±52.0 Y  (2.0 mm offset)
; 2nd skirting (inner): ±51.0 X, ±51.0 Y  (1.0 mm offset)
; Z working depth     : -12.4 mm
; Pause before scan   : 90 seconds
; ════════════════════════════════════════════════════════════

; ─── FIRST SKIRTING LOOP (outer, larger rectangle) ───
G0 X-52.0 Y-52.0  ; move to 1st skirt corner (front-left)
G0 Z-12.4  ; Z down to working depth
; trace 1st rectangle
G1 X52.0 Y-52.0  ; → front-right
G1 X52.0 Y52.0  ; → back-right
G1 X-52.0 Y52.0  ; → back-left
G1 X-52.0 Y-52.0  ; → front-left (close loop)
G0 Z0  ; Z up to safe height

; ─── SECOND SKIRTING LOOP (inner, smaller rectangle) ───
G0 X-51.0 Y-51.0  ; move to 2nd skirt corner (front-left)
G0 Z-12.4  ; Z down to working depth
; trace 2nd rectangle
G1 X51.0 Y-51.0  ; → front-right
G1 X51.0 Y51.0  ; → back-right
G1 X-51.0 Y51.0  ; → back-left
G1 X-51.0 Y-51.0  ; → front-left (close loop)
G0 Z0  ; Z up to safe height

; ─── END SKIRTING, BEFORE SCAN ───
G4 P90000  ; PAUSE 90 seconds for adjustment
; ────────────────────────────────────────────────────

; ════════════════════════════════════════════════════════════
; SCAN LINES — Serpentine X (horizontal lines stepping in Y)
; Sub-region: X-25.0+50.0, Y-25.0+50.0
; Z depth: -12.4 mm
; ════════════════════════════════════════════════════════════
G0 X-25.0 Y-25.0  ; line 1 start →
G1 X25.0 Y-25.0  ; line 1 scan
G0 X25.0 Y-23.0  ; line 2 start ←
G1 X-25.0 Y-23.0  ; line 2 scan
G0 X-25.0 Y-21.0  ; line 3 start →
G1 X25.0 Y-21.0  ; line 3 scan
G0 X25.0 Y-19.0  ; line 4 start ←
G1 X-25.0 Y-19.0  ; line 4 scan
G0 X-25.0 Y-17.0  ; line 5 start →
G1 X25.0 Y-17.0  ; line 5 scan
G0 X25.0 Y-15.0  ; line 6 start ←
G1 X-25.0 Y-15.0  ; line 6 scan
G0 X-25.0 Y-13.0  ; line 7 start →
G1 X25.0 Y-13.0  ; line 7 scan
G0 X25.0 Y-11.0  ; line 8 start ←
G1 X-25.0 Y-11.0  ; line 8 scan
G0 X-25.0 Y-9.0  ; line 9 start →
G1 X25.0 Y-9.0  ; line 9 scan
G0 X25.0 Y-7.0  ; line 10 start ←
G1 X-25.0 Y-7.0  ; line 10 scan
G0 X-25.0 Y-5.0  ; line 11 start →
G1 X25.0 Y-5.0  ; line 11 scan
G0 X25.0 Y-3.0  ; line 12 start ←
G1 X-25.0 Y-3.0  ; line 12 scan
G0 X-25.0 Y-1.0  ; line 13 start →
G1 X25.0 Y-1.0  ; line 13 scan
G0 X25.0 Y1.0  ; line 14 start ←
G1 X-25.0 Y1.0  ; line 14 scan
G0 X-25.0 Y3.0  ; line 15 start →
G1 X25.0 Y3.0  ; line 15 scan
G0 X25.0 Y5.0  ; line 16 start ←
G1 X-25.0 Y5.0  ; line 16 scan
G0 X-25.0 Y7.0  ; line 17 start →
G1 X25.0 Y7.0  ; line 17 scan
G0 X25.0 Y9.0  ; line 18 start ←
G1 X-25.0 Y9.0  ; line 18 scan
G0 X-25.0 Y11.0  ; line 19 start →
G1 X25.0 Y11.0  ; line 19 scan
G0 X25.0 Y13.0  ; line 20 start ←
G1 X-25.0 Y13.0  ; line 20 scan
G0 X-25.0 Y15.0  ; line 21 start →
G1 X25.0 Y15.0  ; line 21 scan
G0 X25.0 Y17.0  ; line 22 start ←
G1 X-25.0 Y17.0  ; line 22 scan
G0 X-25.0 Y19.0  ; line 23 start →
G1 X25.0 Y19.0  ; line 23 scan
G0 X25.0 Y21.0  ; line 24 start ←
G1 X-25.0 Y21.0  ; line 24 scan
G0 X-25.0 Y23.0  ; line 25 start →
G1 X25.0 Y23.0  ; line 25 scan

; ────────────────────────────────────────────────────
; END OF SCAN
G0 Z0      ; move Z back to safe height
G0 X0 Y0   ; return to center origin
M84 S0     ; disable motors
