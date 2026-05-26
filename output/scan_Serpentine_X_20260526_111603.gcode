; ═══════════════════════════════════════════════════
; GCode — Plate Scanning
; Machine    : Anycubic Mega X
; Pattern    : Serpentine X
; Plate      : 100.0 × 100.0 mm
; Edge offset: 1.0 mm
; Scan area  : X1.0+98.0  Y1.0+98.0 mm
; Gap        : 5.0 mm  |  Lines: 20
; Speed      : 65.0 mm/s  (3900.0 mm/min)
; Skirting   : Yes — 2 passes, 60s dwell
; Generated  : 2026-05-26 11:16:03
; ═══════════════════════════════════════════════════
G90          ; Absolute positioning
G21          ; Units: mm
F3900.0  ; Feedrate
G0 X0 Y0     ; Home to origin

; ─── Skirting ────────────────────────────────
; 2 passes at 3.0 mm inset from scan boundary
; Left-front corner dwell: 60 s
G0 X4.0 Y4.0    ; → left-front corner of skirt
G4 P60000  ; wait 60 seconds
; skirt pass 1
G1 X96.0 Y4.0
G1 X96.0 Y96.0
G1 X4.0 Y96.0
G1 X4.0 Y4.0
; skirt pass 2
G1 X96.0 Y4.0
G1 X96.0 Y96.0
G1 X4.0 Y96.0
G1 X4.0 Y4.0
; ─── End Skirting ────────────────────────────

; ─── Serpentine X (lines along X, stepping in Y) ───
G0 X1.0 Y1.0  ; line 1 start
G1 X99.0 Y1.0  ; line 1 end
G0 X99.0 Y6.0  ; line 2 start
G1 X1.0 Y6.0  ; line 2 end
G0 X1.0 Y11.0  ; line 3 start
G1 X99.0 Y11.0  ; line 3 end
G0 X99.0 Y16.0  ; line 4 start
G1 X1.0 Y16.0  ; line 4 end
G0 X1.0 Y21.0  ; line 5 start
G1 X99.0 Y21.0  ; line 5 end
G0 X99.0 Y26.0  ; line 6 start
G1 X1.0 Y26.0  ; line 6 end
G0 X1.0 Y31.0  ; line 7 start
G1 X99.0 Y31.0  ; line 7 end
G0 X99.0 Y36.0  ; line 8 start
G1 X1.0 Y36.0  ; line 8 end
G0 X1.0 Y41.0  ; line 9 start
G1 X99.0 Y41.0  ; line 9 end
G0 X99.0 Y46.0  ; line 10 start
G1 X1.0 Y46.0  ; line 10 end
G0 X1.0 Y51.0  ; line 11 start
G1 X99.0 Y51.0  ; line 11 end
G0 X99.0 Y56.0  ; line 12 start
G1 X1.0 Y56.0  ; line 12 end
G0 X1.0 Y61.0  ; line 13 start
G1 X99.0 Y61.0  ; line 13 end
G0 X99.0 Y66.0  ; line 14 start
G1 X1.0 Y66.0  ; line 14 end
G0 X1.0 Y71.0  ; line 15 start
G1 X99.0 Y71.0  ; line 15 end
G0 X99.0 Y76.0  ; line 16 start
G1 X1.0 Y76.0  ; line 16 end
G0 X1.0 Y81.0  ; line 17 start
G1 X99.0 Y81.0  ; line 17 end
G0 X99.0 Y86.0  ; line 18 start
G1 X1.0 Y86.0  ; line 18 end
G0 X1.0 Y91.0  ; line 19 start
G1 X99.0 Y91.0  ; line 19 end
G0 X99.0 Y96.0  ; line 20 start
G1 X1.0 Y96.0  ; line 20 end

G0 X0 Y0     ; Return to origin
M30          ; End program