import pytest

from fixtures import PCB, SCH
from pufdfm import kicad


def test_schematic_parts_are_sorted_naturally_and_power_symbols_are_not_parts():
    parts, meta = kicad.parse_schematic(SCH)
    assert [p["ref"] for p in parts] == ["C1", "R2", "R10", "TP1"]
    assert meta == {"title": "Test board", "rev": "B", "company": "Nobody"}


def test_library_symbols_inside_lib_symbols_are_not_counted_as_parts():
    parts, _ = kicad.parse_schematic(SCH)
    assert all(p["ref"] != "R" for p in parts)


def test_do_not_populate_and_bom_flags_are_read():
    parts, _ = kicad.parse_schematic(SCH)
    by = {p["ref"]: p for p in parts}
    assert by["C1"]["dnp"] is True and by["R2"]["dnp"] is False
    assert by["TP1"]["in_bom"] is False and by["R2"]["in_bom"] is True


def test_a_rotated_footprint_puts_its_pads_where_kicad_puts_them():
    pcb = kicad.parse_pcb(PCB)
    j = next(f for f in pcb["footprints"] if f["ref"] == "J")
    p1, p2 = j["pads"]
    assert (round(p1["x"], 6), round(p1["y"], 6)) == (10.0, 19.0)         # 90 degrees counter-clockwise on screen: right becomes up (y decreases)
    assert (round(p2["x"], 6), round(p2["y"], 6)) == (10.0, 16.46)
    assert p1["rot"] == 90.0


@pytest.mark.parametrize("deg,expect", [(0, (1, 0)), (90, (0, -1)), (180, (-1, 0)), (270, (0, 1))])
def test_rotation_in_the_four_quarter_turns(deg, expect):
    x, y = kicad.rotate_point(1, 0, deg)
    assert (round(x, 9), round(y, 9)) == expect


def test_pads_tracks_vias_outline_and_text_are_read():
    pcb = kicad.parse_pcb(PCB)
    assert len(pcb["footprints"]) == 3 and len(pcb["segments"]) == 2 and len(pcb["vias"]) == 1 and pcb["zones"] == 0
    assert pcb["outline"] == (100.0, 60.0, 150.8, 84.5)
    q = next(f for f in pcb["footprints"] if f["ref"] == "Q1")
    assert [p["drill"] for p in q["pads"]] == [0.75] * 3 and q["pads"][0]["net"] == "GND"
    r = next(f for f in pcb["footprints"] if f["ref"] == "R3")
    assert r["pads"][0]["rratio"] == 0.25 and r["pads"][0]["drill"] == 0.0
    assert [(t["height"], t["thickness"]) for t in pcb["texts"]] == [(1.0, 0.15), (0.8, 0.12), (0.9, 0.15), (1.0, 0.14)]


def test_a_library_footprint_without_a_position_is_read_at_the_origin():
    lib = '(footprint "X" (layer "F.Cu") (property "Reference" "REF**" (at 0 0 0)) (pad "1" thru_hole rect (at 1.27 0) (size 1 1) (drill 0.6) (layers "*.Cu" "*.Mask")))'
    fp = kicad.parse_pcb("(kicad_pcb " + lib + ")")["footprints"][0]
    assert (fp["x"], fp["y"], fp["rot"]) == (0.0, 0.0, 0.0) and (fp["pads"][0]["x"], fp["pads"][0]["y"]) == (1.27, 0.0)


def test_an_older_style_module_footprint_is_read_too():
    old = "(module TO-92_Inline (layer F.Cu) (pad 1 thru_hole rect (at 0 0) (size 1.05 1.5) (drill 0.75) (layers *.Cu *.Mask)) (pad 2 thru_hole oval (at 1.27 0) (size 1.05 1.5) (drill 0.75) (layers *.Cu *.Mask)))"
    fp = kicad.parse_pcb("(kicad_pcb " + old + ")")["footprints"][0]
    assert fp["name"] == "TO-92_Inline" and [p["x"] for p in fp["pads"]] == [0.0, 1.27] and fp["pads"][0]["drill"] == 0.75


def test_a_drill_with_an_offset_or_an_oval_size_is_read_by_its_first_number():
    lib = ('(footprint "X" (layer "F.Cu") (pad "1" thru_hole oval (at 0 0) (size 1.5 2) (drill 0.8 (offset 0 0.5)) (layers "*.Cu" "*.Mask"))'
           ' (pad "2" thru_hole oval (at 3 0) (size 1.5 2) (drill oval 0.8 1.2) (layers "*.Cu" "*.Mask")))')
    pads = kicad.parse_pcb("(kicad_pcb " + lib + ")")["footprints"][0]["pads"]
    assert [p["drill"] for p in pads] == [0.8, 0.8]
