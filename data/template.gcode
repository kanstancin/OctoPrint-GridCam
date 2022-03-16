G90
G92 E0
T0
M82
;M42 M1 P74 S0 ; set fan to 0 for first layers - TEMP SETTING
;M140 S60
G28 X; home x
G0 X320; move x 35mm off rail for y home
G28 Y ;home y
G1 X177.5 Y177.5 F3600; move to center for Z home
;M190 S60 ; wait for bed to heat
;M109 S160
G28 Z ; home z
G0 Z10 F120;
G29; Mesh level
;M104 S210 ; heat extruder
G0 Y345 X345 ;move back
;M109 S210 ; wait for extruder to heat
;G1 X300 Y355 F2400
G92 E0  ; set extruder to 0 position
G1 X345 Y345 Z0.75; ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
G1 X177.5 Y177.5 F1000.0
;G1 X345 Y345 Z0.75 F1000.0 ; prepare to prime
;G1 X285 E9.0  F1000.0 ; priming
;G1 X245 E12.5  F1000.0 ; priming
;G1 X177.5 Y177.5 F3600;
G92 E0
M82
G92 E0
;G1 E-1 F1800 ; destring suck
G92 E0
;
; *** Main G-code ***
;
; BEGIN_LAYER_OBJECT z=0.5200 z_thickness=0.2000
;
;M211 S0
; *** Selecting and Warming Extruder 1 to 210 degrees C ***
;T0
;M104 S210 T0
;
;
;
; 'Loop Path', 0.9 [feed mm/s], 25.0 [head mm/s]
; inner perimeter
;G1 X359.307 Y332.078 Z0.72 F7200
G1 X359.307 Y332.078 Z0.72 F1000 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; *** Layer Change ***
; layer 1, Z = 0.52
;
;G1 X359.307 Y332.078 Z0.52 F1200
; 'Destring Prime'
;G1 E1 F1800
; head speed 25.000000, filament speed 0.888669, preload 0.000000
; path_width=0.4500

;;;!! This line triggers python generator; Main gcode is below










;;;!! This line triggers python generator

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; 'Destring/Wipe/Jump Path', 0.0 [feed mm/s], 60.0 [head mm/s]
; travel
; 'Destring Suck'
;G1 E29.94287 F1800
; head speed 60.000000, filament speed 0.000000, preload 0.000000
; path_width=0.4500
; Prepare for End-Of-Layer
; time estimate: pre = 29.117254 s, post = 23.305908 s
; Dwell time remaining = -18.305908 s
;
; Post-layer lift
; G1 X359.206 Y331.192 Z20.92 F1200
; END_LAYER_OBJECT z=20.320
;
; *** Cooling Extruder 1 to 0 degrees C and Retiring ***
;
;
; fan off
M107
; *** G-code Postfix ***
;
G90; set to absolute positioning
G1 X359.206
G0 Y345 F300;
;G0 Z345 F600; BED TO GANTRY POSITION
M104 S0 ; turn off extruder
M140 S0 ; turn off bed
M84; disable motors
M42 M1 P74 S0 ; disable fan to 0 for first layers - TEMP SETTING