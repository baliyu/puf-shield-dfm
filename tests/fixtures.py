"""Small KiCad-style text fixtures: invented, not taken from any real board (one pad and track reproduce a measurement made on a real board, see test_checks)."""

SCH = """(kicad_sch
\t(version 20260306)
\t(title_block (title "Test board") (rev "B") (company "Nobody"))
\t(lib_symbols
\t\t(symbol "Device:R" (property "Reference" "R" (at 0 0 0)) (symbol "R_0_1")))
\t(symbol (lib_id "Device:R") (at 1 1 0) (dnp no) (in_bom yes) (on_board yes)
\t\t(property "Reference" "R10" (at 0 0 0)) (property "Value" "100k" (at 0 0 0)) (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at 0 0 0)))
\t(symbol (lib_id "Device:R") (at 2 2 0) (dnp no) (in_bom yes) (on_board yes)
\t\t(property "Reference" "R2" (at 0 0 0)) (property "Value" "100k" (at 0 0 0)) (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at 0 0 0)))
\t(symbol (lib_id "Device:C") (at 3 3 0) (dnp yes) (in_bom yes) (on_board yes)
\t\t(property "Reference" "C1" (at 0 0 0)) (property "Value" "10u" (at 0 0 0)) (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at 0 0 0)))
\t(symbol (lib_id "power:GND") (at 4 4 0) (dnp no) (in_bom yes) (on_board yes)
\t\t(property "Reference" "#PWR01" (at 0 0 0)) (property "Value" "GND" (at 0 0 0)))
\t(symbol (lib_id "Connector:Test") (at 5 5 0) (dnp no) (in_bom no) (on_board yes)
\t\t(property "Reference" "TP1" (at 0 0 0)) (property "Value" "TP" (at 0 0 0)) (property "Footprint" "" (at 0 0 0)))
)
"""

# R3: a roundrect 0805 pad on 3V3 and a GND track passing its rounded corner (numbers measured on a real board: 0.099 mm if the corner is
# wrongly taken as square, about 0.205 mm with the rounded corner); J: a rotated header; Q: TO-92 inline at 1.27 mm pitch
PCB = """(kicad_pcb
\t(version 20260206)
\t(general (thickness 1.6))
\t(footprint "Resistor_SMD:R_0805_2012Metric" (layer "F.Cu") (at 140 70)
\t\t(property "Reference" "R3" (at 0 -1.5 0) (layer "F.SilkS"))
\t\t(pad "1" smd roundrect (at -0.912 0) (size 1.025 1.4) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net "+3V3"))
\t\t(pad "2" smd roundrect (at 0.912 0) (size 1.025 1.4) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25) (net "/TEMP_DQ")))
\t(footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" (layer "F.Cu") (at 10 20 90)
\t\t(property "Reference" "J" (at 0 0 0) (layer "F.SilkS"))
\t\t(pad "1" thru_hole rect (at 1 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net "GND"))
\t\t(pad "2" thru_hole oval (at 3.54 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net "/SIG")))
\t(footprint "Package_TO_SOT_THT:TO-92_Inline" (layer "F.Cu") (at 112.8 73)
\t\t(property "Reference" "Q1" (at 1.27 -3.56 0) (layer "F.SilkS"))
\t\t(pad "1" thru_hole rect (at 0 0) (size 1.05 1.5) (drill 0.75) (layers "*.Cu" "*.Mask") (net "GND"))
\t\t(pad "2" thru_hole oval (at 1.27 0) (size 1.05 1.5) (drill 0.75) (layers "*.Cu" "*.Mask") (net "/GATE"))
\t\t(pad "3" thru_hole oval (at 2.54 0) (size 1.05 1.5) (drill 0.75) (layers "*.Cu" "*.Mask") (net "/SW")))
\t(segment (start 139.5788 71.0027) (end 139.9027 70.6788) (width 0.2) (layer "F.Cu") (net "GND"))
\t(segment (start 102 61) (end 105 61) (width 0.2) (layer "F.Cu") (net "/SIG"))
\t(via (at 120 61) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "/SIG"))
\t(gr_rect (start 100 60) (end 150.8 84.5) (stroke (width 0.05) (type default)) (fill no) (layer "Edge.Cuts"))
\t(gr_text "BIG" (at 1 1 0) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15))))
\t(gr_text "small" (at 2 2 0) (layer "B.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
\t(gr_text "short" (at 3 3 0) (layer "B.SilkS") (effects (font (size 0.9 0.9) (thickness 0.15))))
\t(gr_text "thin" (at 4 4 0) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.14))))
)
"""

DRILL = """M48
; DRILL file
METRIC
T1C0.300
T2C0.750
%
G90
T1
X120.0Y-61.0
T2
X112.8Y-73.0
X114.07Y-73.0
X115.34Y-73.0
M30
"""
