import subprocess
import sys

import pytest

from fixtures import DRILL, PCB, SCH
from pufdfm import bom, drill, kicad


def test_drill_file_is_read_with_tool_sizes():
    h = drill.read_drill(DRILL)
    assert h == [(120.0, -61.0, 0.3), (112.8, -73.0, 0.75), (114.07, -73.0, 0.75), (115.34, -73.0, 0.75)]


def drill_holes():
    return drill.read_drill(DRILL)


def pcb_without_the_header():
    pcb = kicad.parse_pcb(PCB)
    pcb["footprints"] = [f for f in pcb["footprints"] if f["ref"] != "J"]
    return pcb


def test_identical_hole_patterns_compare_clean():
    assert drill.compare(pcb_without_the_header(), drill_holes()) == ([], [])


def test_a_hole_in_the_pcb_that_is_not_in_the_drill_file_is_reported():
    missing, extra = drill.compare(kicad.parse_pcb(PCB), drill_holes())
    assert {m[0] for m in missing} == {"J.1", "J.2"} and extra == []


def test_a_drill_file_hole_the_pcb_does_not_have_is_reported():
    pcb = pcb_without_the_header()
    pcb["footprints"] = [f for f in pcb["footprints"] if f["ref"] != "Q1"]
    missing, extra = drill.compare(pcb, drill_holes())
    assert len(extra) == 3 and {m[0] for m in missing} == set()


def test_a_wrong_diameter_or_position_is_not_a_match():
    h = drill_holes()
    h[1] = (h[1][0], h[1][1], 0.8)
    assert drill.compare(pcb_without_the_header(), h)[0][0][0] == "Q1.1"
    h = drill_holes()
    h[0] = (h[0][0] + 0.01, h[0][1], h[0][2])
    assert drill.compare(pcb_without_the_header(), h)[0][0][0] == "via0"


def test_the_pcbs_y_axis_is_flipped_for_the_drill_file():
    flipped = [(x, -y, d) for x, y, d in drill_holes()]                                    # as if y were not negated
    assert drill.compare(pcb_without_the_header(), flipped)[0] != []


def test_bom_groups_identical_parts_and_keeps_dnp_parts_apart_and_drops_parts_not_in_the_bom():
    parts, _ = kicad.parse_schematic(SCH)
    rows = bom.group(parts)
    assert [(r["refs"], r["qty"], r["dnp"]) for r in rows] == [("C1", 1, "yes"), ("R2, R10", 2, "no")]


def test_bom_csv_has_the_requested_columns_only():
    parts, _ = kicad.parse_schematic(SCH)
    text = bom.to_csv(bom.group(parts), ["refs", "qty", "value", "footprint", "dnp"])
    assert text.splitlines()[0] == "refs,qty,value,footprint,dnp" and '"R2, R10"' in text


def test_command_line_report_and_bom(tmp_path):
    (tmp_path / "t.kicad_sch").write_text(SCH, encoding="utf-8")
    (tmp_path / "t.kicad_pcb").write_text(PCB, encoding="utf-8")
    (tmp_path / "g").mkdir()
    (tmp_path / "g" / "t-PTH.drl").write_text(DRILL, encoding="utf-8")
    run = lambda *a: subprocess.run([sys.executable, "-m", "pufdfm", *a], capture_output=True, text=True, check=True).stdout
    out = run("report", "--project", str(tmp_path), "--gerbers", str(tmp_path / "g"))
    assert "Test board, rev B: 4 parts" in out and "do-not-populate in the schematic: C1" in out
    assert "silkscreen text below 1.0 mm height or 0.15 mm line width: 3 of 4" in out      # 0.8/0.12 fails both, 0.9/0.15 only the height, 1.0/0.14 only the line width
    assert "PCB holes missing from the drill files: [('J.1'" in out and "drill-file holes missing from the PCB: none" in out
    assert "holes: PCB file 6, drill files 4 (t-PTH.drl)" in out
    assert run("bom", "--project", str(tmp_path)).splitlines()[0] == "refs,qty,value,footprint,dnp"
