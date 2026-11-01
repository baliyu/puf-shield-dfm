"""Compares the holes in a PCB file with an Excellon drill file, the part of 'is this the board that was made' that can be checked from text."""
from __future__ import annotations

import re


def read_drill(text):
    """[(x, y, diameter)] from a KiCad Excellon file (metric, absolute coordinates, y pointing up)."""
    holes, tools, cur = [], {}, None
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"T(\d+)C([\d.]+)", line)
        if m:
            tools[m.group(1)] = float(m.group(2))
            continue
        m = re.match(r"^T(\d+)$", line)
        if m:
            cur = tools[m.group(1)]
            continue
        m = re.match(r"^X([-\d.]+)Y([-\d.]+)", line)
        if m and cur is not None:
            holes.append((float(m.group(1)), float(m.group(2)), cur))
    return holes


def pcb_holes(pcb):
    """The PCB's holes in the drill file's coordinates (KiCad's PCB y points down, the drill file's up)."""
    out = [(p["x"], -p["y"], p["drill"], f"{f['ref']}.{p['number']}") for f in pcb["footprints"] for p in f["pads"] if p["drill"] > 0]
    out += [(v["x"], -v["y"], v["drill"], f"via{i}") for i, v in enumerate(pcb["vias"])]
    return out


def compare(pcb, drill_holes, tol_pos=0.003, tol_dia=0.001):
    """(PCB holes missing from the drill file, drill-file holes the PCB does not have). Both empty means the hole patterns are identical."""
    free = list(range(len(drill_holes)))
    missing = []
    for x, y, d, name in pcb_holes(pcb):
        hit = next((i for i in free if abs(drill_holes[i][0] - x) < tol_pos and abs(drill_holes[i][1] - y) < tol_pos
                    and abs(drill_holes[i][2] - d) < tol_dia), None)
        if hit is None:
            missing.append((name, round(x, 3), round(y, 3), d))
        else:
            free.remove(hit)
    return missing, [drill_holes[i] for i in free]
