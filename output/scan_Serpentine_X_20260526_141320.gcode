; ═══════════════════════════════════════════════════
; GCode — Plate Scanning
; Machine    : Anycubic Mega X
; Pattern    : Serpentine X
; Plate      : 100.0 × 100.0 mm
; Edge offset: 2.0 mm
; Scan area  : X2.0+96.0  Y2.0+96.0 mm
; Gap        : 2.0 mm  |  Lines: 49
; Speed      : 80.0 mm/s  (4800.0 mm/min)
; Skirting   : Yes — 2 passes, 60s dwell
; Generated  : 2026-05-26 14:13:20
; ═══════════════════════════════════════════════════
G90          ; Absolute positioning
G21          ; Units: mm
F4800.0  ; Feedrate
G0 X0 Y0     ; Home to origin

; ─── Skirting ────────────────────────────────
; 2 passes at 3.0 mm inset from scan boundary
; Left-front corner dwell: 60 s
G0 X5.0 Y5.0    ; → left-front corner of skirt
G4 P60000  ; wait 60 seconds
; skirt pass 1
G1 X95.0 Y5.0
G1 X95.0 Y95.0
G1 X5.0 Y95.0
G1 X5.0 Y5.0
; skirt pass 2
G1 X95.0 Y5.0
G1 X95.0 Y95.0
G1 X5.0 Y95.0
G1 X5.0 Y5.0
; ─── End Skirting ────────────────────────────

; ─── Serpentine X (lines along X, stepping in Y) ───
G0 X2.0 Y2.0  ; line 1 start
G1 X98.0 Y2.0  ; line 1 end
G0 X98.0 Y4.0  ; line 2 start
G1 X2.0 Y4.0  ; line 2 end
G0 X2.0 Y6.0  ; line 3 start
G1 X98.0 Y6.0  ; line 3 end
G0 X98.0 Y8.0  ; line 4 start
G1 X2.0 Y8.0  ; line 4 end
G0 X2.0 Y10.0  ; line 5 start
G1 X98.0 Y10.0  ; line 5 end
G0 X98.0 Y12.0  ; line 6 start
G1 X2.0 Y12.0  ; line 6 end
G0 X2.0 Y14.0  ; line 7 start
G1 X98.0 Y14.0  ; line 7 end
G0 X98.0 Y16.0  ; line 8 start
G1 X2.0 Y16.0  ; line 8 end
G0 X2.0 Y18.0  ; line 9 start
G1 X98.0 Y18.0  ; line 9 end
G0 X98.0 Y20.0  ; line 10 start
G1 X2.0 Y20.0  ; line 10 end
G0 X2.0 Y22.0  ; line 11 start
G1 X98.0 Y22.0  ; line 11 end
G0 X98.0 Y24.0  ; line 12 start
G1 X2.0 Y24.0  ; line 12 end
G0 X2.0 Y26.0  ; line 13 start
G1 X98.0 Y26.0  ; line 13 end
G0 X98.0 Y28.0  ; line 14 start
G1 X2.0 Y28.0  ; line 14 end
G0 X2.0 Y30.0  ; line 15 start
G1 X98.0 Y30.0  ; line 15 end
G0 X98.0 Y32.0  ; line 16 start
G1 X2.0 Y32.0  ; line 16 end
G0 X2.0 Y34.0  ; line 17 start
G1 X98.0 Y34.0  ; line 17 end
G0 X98.0 Y36.0  ; line 18 start
G1 X2.0 Y36.0  ; line 18 end
G0 X2.0 Y38.0  ; line 19 start
G1 X98.0 Y38.0  ; line 19 end
G0 X98.0 Y40.0  ; line 20 start
G1 X2.0 Y40.0  ; line 20 end
G0 X2.0 Y42.0  ; line 21 start
G1 X98.0 Y42.0  ; line 21 end
G0 X98.0 Y44.0  ; line 22 start
G1 X2.0 Y44.0  ; line 22 end
G0 X2.0 Y46.0  ; line 23 start
G1 X98.0 Y46.0  ; line 23 end
G0 X98.0 Y48.0  ; line 24 start
G1 X2.0 Y48.0  ; line 24 end
G0 X2.0 Y50.0  ; line 25 start
G1 X98.0 Y50.0  ; line 25 end
G0 X98.0 Y52.0  ; line 26 start
G1 X2.0 Y52.0  ; line 26 end
G0 X2.0 Y54.0  ; line 27 start
G1 X98.0 Y54.0  ; line 27 end
G0 X98.0 Y56.0  ; line 28 start
G1 X2.0 Y56.0  ; line 28 end
G0 X2.0 Y58.0  ; line 29 start
G1 X98.0 Y58.0  ; line 29 end
G0 X98.0 Y60.0  ; line 30 start
G1 X2.0 Y60.0  ; line 30 end
G0 X2.0 Y62.0  ; line 31 start
G1 X98.0 Y62.0  ; line 31 end
G0 X98.0 Y64.0  ; line 32 start
G1 X2.0 Y64.0  ; line 32 end
G0 X2.0 Y66.0  ; line 33 start
G1 X98.0 Y66.0  ; line 33 end
G0 X98.0 Y68.0  ; line 34 start
G1 X2.0 Y68.0  ; line 34 end
G0 X2.0 Y70.0  ; line 35 start
G1 X98.0 Y70.0  ; line 35 end
G0 X98.0 Y72.0  ; line 36 start
G1 X2.0 Y72.0  ; line 36 end
G0 X2.0 Y74.0  ; line 37 start
G1 X98.0 Y74.0  ; line 37 end
G0 X98.0 Y76.0  ; line 38 start
G1 X2.0 Y76.0  ; line 38 end
G0 X2.0 Y78.0  ; line 39 start
G1 X98.0 Y78.0  ; line 39 end
G0 X98.0 Y80.0  ; line 40 start
G1 X2.0 Y80.0  ; line 40 end
G0 X2.0 Y82.0  ; line 41 start
G1 X98.0 Y82.0  ; line 41 end
G0 X98.0 Y84.0  ; line 42 start
G1 X2.0 Y84.0  ; line 42 end
G0 X2.0 Y86.0  ; line 43 start
G1 X98.0 Y86.0  ; line 43 end
G0 X98.0 Y88.0  ; line 44 start
G1 X2.0 Y88.0  ; line 44 end
G0 X2.0 Y90.0  ; line 45 start
G1 X98.0 Y90.0  ; line 45 end
G0 X98.0 Y92.0  ; line 46 start
G1 X2.0 Y92.0  ; line 46 end
G0 X2.0 Y94.0  ; line 47 start
G1 X98.0 Y94.0  ; line 47 end
G0 X98.0 Y96.0  ; line 48 start
G1 X2.0 Y96.0  ; line 48 end
G0 X2.0 Y98.0  ; line 49 start
G1 X98.0 Y98.0  ; line 49 end

G0 X0 Y0     ; Return to origin
M30          ; End program