import subprocess
import sys
from pathlib import Path

import pytest

from pufdfm import costing

ROOT = Path(__file__).resolve().parents[1]
HEAD = ",".join(costing.COLUMNS) + "\n"


def row(refs="A", per=1, fitted="yes", breaks="", cur="GBP"):
    if breaks:
        return f"{refs},{per},{fitted},d,m,Shop,{cur},{breaks},http://x,2026-11-01,live page,,\n"
    return f"{refs},{per},{fitted},d,m,,,,,,,,\n"


def table(*rows):
    return costing.load(HEAD + "".join(rows))


def test_breaks_parse_and_an_empty_cell_means_no_price():
    assert costing.parse_breaks("1:0.61;25:0.5976;100:0.5753") == [(1, 0.61), (25, 0.5976), (100, 0.5753)]
    assert costing.parse_breaks("") == [] and costing.parse_breaks(None) == []


@pytest.mark.parametrize("bad", ["25:1;1:2", "1:1;1:2", "x:1", "1"])
def test_bad_breaks_are_rejected(bad):
    with pytest.raises(ValueError):
        costing.parse_breaks(bad)


@pytest.mark.parametrize("qty,expect", [(1, 0.61), (24, 0.61), (25, 0.5976), (99, 0.5976), (100, 0.5753), (5000, 0.5753)])
def test_unit_price_uses_the_highest_break_not_above_the_quantity(qty, expect):
    assert costing.unit_price(costing.parse_breaks("1:0.61;25:0.5976;100:0.5753"), qty) == expect


def test_below_the_first_break_the_first_price_applies():
    assert costing.unit_price(costing.parse_breaks("10:0.44;50:0.34"), 2) == 0.44


def test_cost_multiplies_by_parts_per_board_and_by_boards_for_the_break():
    rows = table(row("U", 2, breaks="1:0.61;25:0.5976;100:0.5753"))
    assert costing.cost(rows, 1)[0] == pytest.approx(1.22)
    assert costing.cost(rows, 10)[0] == pytest.approx(1.22)              # 20 chips: still below the 25 break
    assert costing.cost(rows, 13)[0] == pytest.approx(2 * 0.5976)        # 26 chips: the 25 break applies
    assert costing.cost(rows, 50)[0] == pytest.approx(2 * 0.5753)        # 100 chips: the 100 break applies


def test_parts_without_a_price_are_listed_and_never_counted_as_free():
    rows = table(row("P", 1, breaks="1:1.00"), row("X", 1))
    total, lines, unpriced, cur = costing.cost(rows, 1)
    assert total == 1.0 and unpriced == ["X"] and [l[0] for l in lines] == ["P"] and cur == {"GBP"}


def test_parts_not_fitted_are_left_out_of_the_cost_and_of_the_unpriced_list():
    rows = table(row("P", 1, breaks="1:1.00"), row("N", 1, fitted="no", breaks="1:5.00"), row("M", 1, fitted="no"))
    total, lines, unpriced, _ = costing.cost(rows, 1)
    assert total == 1.0 and unpriced == [] and len(lines) == 1


def test_validation_finds_missing_provenance_and_bad_fields():
    assert costing.validate(table(row("P", 1, breaks="1:1.00"))) == []
    no_src = costing.load(HEAD + "P,1,yes,d,m,Shop,GBP,1:1.00,,2026-11-01,live page,,\n")
    assert any("needs source" in p for p in costing.validate(no_src))
    assert any("fitted must be" in p for p in costing.validate(table(row("P", 1, fitted="maybe"))))
    assert any("per_board" in p for p in costing.validate(table(row("P", 0))))
    assert any("rise in quantity" in p for p in costing.validate(table(row("P", 1, breaks="5:1;2:2"))))


def test_the_committed_costed_bom_is_valid_and_every_price_has_its_source_date_and_confidence():
    rows = costing.load((ROOT / "bom" / "puf_shield_costed.csv").read_text(encoding="utf-8"))
    assert costing.validate(rows) == []
    priced = [r for r in rows if r["breaks"].strip()]
    assert len(priced) >= 3 and all(r["source"].startswith("http") and r["retrieved"] and r["confidence"] in ("live page", "search snippet") for r in priced)


def test_the_committed_bom_lists_unpriced_fitted_parts_instead_of_hiding_them():
    rows = costing.load((ROOT / "bom" / "puf_shield_costed.csv").read_text(encoding="utf-8"))
    _, _, unpriced, _ = costing.cost(rows, 1)
    assert "PCB" in unpriced and "C1, C2" in unpriced


def test_command_line_cost(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text(HEAD + row("U", 2, breaks="1:0.61;25:0.5976") + row("X", 1), encoding="utf-8")
    run = lambda *a: subprocess.run([sys.executable, "-m", "pufdfm", *a], capture_output=True, text=True)
    r = run("cost", str(f), "--boards", "1", "13")
    assert r.returncode == 0 and "1 board(s): 1.22 GBP" in r.stdout and "13 board(s): 1.20 GBP" in r.stdout and "unpriced fitted lines (not counted as free): X" in r.stdout
    f.write_text(HEAD + row("U", 2, breaks="9:1;1:2"), encoding="utf-8")
    r = run("cost", str(f))
    assert r.returncode == 1 and "rise in quantity" in r.stdout
