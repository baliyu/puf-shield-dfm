"""Bill of materials from a parsed schematic: as designed (what the schematic says) and a table to record what was actually fitted."""
from __future__ import annotations

import csv
import io


def group(parts):
    """Rows of {refs, qty, value, footprint, dnp} grouped by value, footprint and DNP flag. Parts not in the BOM are left out."""
    rows = {}
    for p in parts:
        if not p["in_bom"] or not p["on_board"]:
            continue
        key = (p["value"], p["footprint"], p["dnp"])
        rows.setdefault(key, []).append(p["ref"])
    out = [{"refs": ", ".join(r), "qty": len(r), "value": k[0], "footprint": k[1], "dnp": "yes" if k[2] else "no"} for k, r in rows.items()]
    return sorted(out, key=lambda r: r["refs"])


def to_csv(rows, columns):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()
