"""DFMEA table: reads a CSV, checks it, ranks it by risk priority number (severity x occurrence x detection) and writes it as a Markdown table."""
from __future__ import annotations

import csv
import io

COLUMNS = ["id", "item", "failure_mode", "effect", "severity", "cause", "occurrence", "controls", "detection", "evidence_type", "evidence", "action", "finding"]
EVIDENCE_TYPES = ("observed", "photo", "thesis", "design analysis", "judgement")
SCORED = ("severity", "occurrence", "detection")


def load(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows


def validate(rows):
    """List of problems; an empty list means the table is usable."""
    problems = []
    if not rows:
        return ["the table is empty"]
    missing = [c for c in COLUMNS if c not in rows[0]]
    if missing:
        return [f"missing columns: {', '.join(missing)}"]
    seen = set()
    for r in rows:
        rid = r["id"].strip()
        if not rid:
            problems.append("a row has no id")
        elif rid in seen:
            problems.append(f"{rid}: duplicate id")
        seen.add(rid)
        for c in SCORED:
            try:
                v = int(r[c])
            except (TypeError, ValueError):
                problems.append(f"{rid}: {c} is not a whole number ({r[c]!r})")
                continue
            if not 1 <= v <= 10:
                problems.append(f"{rid}: {c} {v} is outside 1 to 10")
        if r["evidence_type"] not in EVIDENCE_TYPES:
            problems.append(f"{rid}: evidence_type {r['evidence_type']!r} is not one of {', '.join(EVIDENCE_TYPES)}")
        for c in ("failure_mode", "effect", "cause", "evidence", "action"):
            if not r[c].strip():
                problems.append(f"{rid}: {c} is empty")
    return problems


def rpn(row):
    return int(row["severity"]) * int(row["occurrence"]) * int(row["detection"])


def ranked(rows):
    """Highest risk priority number first; equal numbers by severity, then id."""
    return sorted(rows, key=lambda r: (-rpn(r), -int(r["severity"]), r["id"]))


def to_markdown(rows):
    head = "| ID | Item | Failure mode | Effect | S | Cause | O | Current controls | D | RPN | Evidence | Action |"
    sep = "|---|---|---|---|---|---|---|---|---|---|---|---|"
    lines = [head, sep]
    for r in ranked(rows):
        lines.append(f"| {r['id']} | {r['item']} | {r['failure_mode']} | {r['effect']} | {r['severity']} | {r['cause']} | {r['occurrence']} | "
                     f"{r['controls']} | {r['detection']} | **{rpn(r)}** | {r['evidence_type']}: {r['evidence']} | {r['action']} |")
    return "\n".join(lines) + "\n"
