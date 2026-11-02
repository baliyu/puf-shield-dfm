"""Cost per board from a priced BOM: unit prices come from supplier price breaks, parts with no price are listed (never counted as free)."""
from __future__ import annotations

import csv
import io

COLUMNS = ["refs", "per_board", "fitted", "description", "mpn", "supplier", "currency", "breaks", "source", "retrieved", "confidence", "alternatives", "notes"]


def parse_breaks(text):
    """'1:0.61;25:0.5976;100:0.5753' -> [(1, 0.61), (25, 0.5976), (100, 0.5753)]; an empty string means no price."""
    text = (text or "").strip()
    if not text:
        return []
    out = []
    for part in text.split(";"):
        q, p = part.split(":")
        out.append((int(q), float(p)))
    if [q for q, _ in out] != sorted({q for q, _ in out}):
        raise ValueError(f"price breaks must rise in quantity with no repeats: {text}")
    return out


def load(text):
    return list(csv.DictReader(io.StringIO(text)))


def validate(rows):
    problems = []
    if not rows:
        return ["the table is empty"]
    missing = [c for c in COLUMNS if c not in rows[0]]
    if missing:
        return [f"missing columns: {', '.join(missing)}"]
    for r in rows:
        name = r["refs"] or "?"
        try:
            if int(r["per_board"]) < 1:
                problems.append(f"{name}: per_board must be at least 1")
        except ValueError:
            problems.append(f"{name}: per_board is not a whole number")
        if r["fitted"] not in ("yes", "no"):
            problems.append(f"{name}: fitted must be yes or no")
        try:
            br = parse_breaks(r["breaks"])
        except ValueError as e:
            problems.append(f"{name}: {e}")
            continue
        if br:
            for c in ("currency", "supplier", "source", "retrieved", "confidence"):
                if not r[c].strip():
                    problems.append(f"{name}: a priced line needs {c}")
    return problems


def unit_price(breaks, qty):
    """Price at the highest break not above the quantity; below the first break the first price is used (that is what a one-off order pays)."""
    price = breaks[0][1]
    for q, p in breaks:
        if qty >= q:
            price = p
    return price


def cost(rows, boards):
    """(priced total for one board, [(refs, unit price, line cost)], [refs of fitted parts with no price], currencies seen)."""
    total, lines, unpriced, cur = 0.0, [], [], set()
    for r in rows:
        if r["fitted"] != "yes":
            continue
        br = parse_breaks(r["breaks"])
        if not br:
            unpriced.append(r["refs"])
            continue
        qty = int(r["per_board"]) * boards
        up = unit_price(br, qty)
        line = up * int(r["per_board"])
        total += line
        lines.append((r["refs"], up, line))
        cur.add(r["currency"])
    return total, lines, unpriced, cur
