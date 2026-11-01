import re
import subprocess
import sys
from pathlib import Path

import pytest

from pufdfm import dfmea

ROOT = Path(__file__).resolve().parents[1]
HEAD = ",".join(dfmea.COLUMNS) + "\n"


def row(i="A1", s=5, o=5, d=5, et="judgement", ev="x", fm="fm", eff="e", cause="c", act="a"):
    return f'{i},item,{fm},{eff},{s},{cause},{o},ctl,{d},{et},{ev},{act},\n'


def table(*rows):
    return dfmea.load(HEAD + "".join(rows))


def test_a_good_table_validates_and_computes_the_rpn():
    rows = table(row("A1", 7, 3, 2), row("B2", 2, 2, 2))
    assert dfmea.validate(rows) == [] and dfmea.rpn(rows[0]) == 42


def test_ranking_is_by_rpn_then_severity_then_id():
    rows = table(row("C", 2, 5, 6), row("B", 6, 5, 2), row("A", 6, 5, 2), row("D", 10, 6, 1))
    assert [r["id"] for r in dfmea.ranked(rows)] == ["D", "A", "B", "C"]         # 60, 60, 60, 60: equal numbers go by severity (10, 6, 6, 2), then id


@pytest.mark.parametrize("bad,expect", [(dict(s=0), "severity 0 is outside"), (dict(o=11), "occurrence 11 is outside"), (dict(d="x"), "detection is not a whole number"),
                                        (dict(et="guess"), "evidence_type"), (dict(ev=""), "evidence is empty"), (dict(cause=""), "cause is empty"),
                                        (dict(act=""), "action is empty"), (dict(fm=""), "failure_mode is empty")])
def test_each_kind_of_bad_row_is_reported(bad, expect):
    problems = dfmea.validate(table(row("A1", **bad)))
    assert any(expect in p for p in problems), problems


def test_duplicate_ids_missing_columns_and_empty_tables_are_reported():
    assert any("duplicate id" in p for p in dfmea.validate(table(row("A1"), row("A1"))))
    assert dfmea.validate(dfmea.load("id,item\nA,b\n"))[0].startswith("missing columns")
    assert dfmea.validate([]) == ["the table is empty"]


def test_markdown_table_has_one_line_per_row_in_rank_order_and_shows_the_evidence_type():
    md = dfmea.to_markdown(table(row("LOW", 1, 1, 1), row("HIGH", 9, 9, 9, et="observed", ev="it happened"))).splitlines()
    assert md[0].startswith("| ID |") and md[2].startswith("| HIGH |") and md[3].startswith("| LOW |")
    assert "**729**" in md[2] and "observed: it happened" in md[2]


def committed():
    return dfmea.load((ROOT / "dfmea" / "puf_shield_dfmea.csv").read_text(encoding="utf-8"))


def test_the_committed_dfmea_is_valid_and_every_row_has_evidence():
    rows = committed()
    assert dfmea.validate(rows) == [] and len(rows) >= 10
    assert all(r["evidence"].strip() for r in rows)


def test_the_observed_events_are_the_ones_i_recorded_and_not_more():
    observed = {r["id"] for r in committed() if r["evidence_type"] == "observed"}
    assert observed == {"D01", "D02"}                                            # only things that happened on this board; everything else is a different kind of evidence


def test_the_table_in_the_document_is_what_the_tool_writes_now():
    doc = (ROOT / "docs" / "DFMEA.md").read_text(encoding="utf-8")
    inside = re.search(r"<!-- table:start -->\n(.*?)<!-- table:end -->", doc, re.S).group(1)
    assert inside == dfmea.to_markdown(committed()), "regenerate: python -m pufdfm dfmea dfmea/puf_shield_dfmea.csv --markdown"


def test_command_line_checks_ranks_and_reports_problems(tmp_path):
    good = tmp_path / "g.csv"
    good.write_text(HEAD + row("A1", 7, 3, 2) + row("B2", 2, 2, 2), encoding="utf-8")
    run = lambda *a: subprocess.run([sys.executable, "-m", "pufdfm", *a], capture_output=True, text=True)
    r = run("dfmea", str(good))
    assert r.returncode == 0 and "2 failure modes" in r.stdout and r.stdout.index("A1") < r.stdout.index("B2")
    bad = tmp_path / "b.csv"
    bad.write_text(HEAD + row("A1", 11, 3, 2), encoding="utf-8")
    r = run("dfmea", str(bad))
    assert r.returncode == 1 and "severity 11 is outside" in r.stdout
