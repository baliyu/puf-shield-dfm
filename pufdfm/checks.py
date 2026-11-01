"""Geometric DFM measurements from a parsed PCB: clearances, annular rings, pad gaps, hole spacing, edge distances."""
from __future__ import annotations

import itertools
import math

from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon, box


def pad_shape(p):
    cx, cy, w, h, rot = p["x"], p["y"], p["w"], p["h"], p["rot"]
    if p["shape"] == "circle":
        return Point(cx, cy).buffer(w / 2, 32)
    if p["shape"] == "oval":
        r = min(w, h) / 2
        d = abs(w - h) / 2
        line = LineString([(cx - d, cy), (cx + d, cy)]) if w >= h else LineString([(cx, cy - d), (cx, cy + d)])
        shp = line.buffer(r, 16)
    elif p["shape"] == "roundrect" and p.get("rratio", 0) > 0:     # rounded corners: radius = ratio x the shorter side
        r = p["rratio"] * min(w, h)
        shp = box(cx - w / 2 + r, cy - h / 2 + r, cx + w / 2 - r, cy + h / 2 - r).buffer(r, 16)
    else:                                                          # rect (square corners) and anything else: the bounding rectangle
        shp = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    return rotate(shp, -rot, origin=(cx, cy)) if rot % 360 else shp


def copper_items(pcb):
    items = []
    for f in pcb["footprints"]:
        for p in f["pads"]:
            layers = set()
            for l in p["layers"]:
                if l == "*.Cu":
                    layers |= {"F.Cu", "B.Cu"}
                elif l in ("F.Cu", "B.Cu"):
                    layers.add(l)
            if layers:
                items.append({"kind": "pad", "name": f"{f['ref']}.{p['number']}", "net": p["net"], "layers": layers, "shape": pad_shape(p), "fp": f["ref"]})
    for i, s in enumerate(pcb["segments"]):
        items.append({"kind": "track", "name": f"track{i}", "net": s["net"], "layers": {s["layer"]}, "fp": None,
                      "shape": LineString([(s["x1"], s["y1"]), (s["x2"], s["y2"])]).buffer(s["width"] / 2, 8)})
    for i, v in enumerate(pcb["vias"]):
        items.append({"kind": "via", "name": f"via{i}", "net": v["net"], "layers": {"F.Cu", "B.Cu"}, "fp": None,
                      "shape": Point(v["x"], v["y"]).buffer(v["size"] / 2, 16)})
    return items


def min_clearances(items, top=10):
    """Smallest gaps between copper of different nets on the same layer. Items on the same net are meant to touch and are skipped."""
    out = []
    for a, b in itertools.combinations(items, 2):
        if a["net"] == b["net"]:
            continue
        common = a["layers"] & b["layers"]
        if not common:
            continue
        d = a["shape"].distance(b["shape"])
        if d < 1.0:
            out.append((d, a["name"], b["name"], sorted(common)))
    out.sort(key=lambda t: t[0])
    return out[:top]


def annular_rings(pcb):
    """(name, ring in mm, pad w, pad h, drill), smallest first. The ring is measured on the narrow side of the pad."""
    rows = []
    for f in pcb["footprints"]:
        for p in f["pads"]:
            if p["drill"] > 0 and p["type"] == "thru_hole":
                rows.append((f"{f['ref']}.{p['number']}", (min(p["w"], p["h"]) - p["drill"]) / 2, p["w"], p["h"], p["drill"]))
    for i, v in enumerate(pcb["vias"]):
        rows.append((f"via{i}", (v["size"] - v["drill"]) / 2, v["size"], v["size"], v["drill"]))
    return sorted(rows, key=lambda r: r[1])


def pad_gaps(pcb):
    """Per footprint: the smallest edge to edge copper gap between two of its pads (the hand-soldering bridge risk), smallest first."""
    rows = []
    for f in pcb["footprints"]:
        shapes = [(p["number"], pad_shape(p)) for p in f["pads"]]
        best = None
        for (n1, s1), (n2, s2) in itertools.combinations(shapes, 2):
            d = s1.distance(s2)
            if best is None or d < best[0]:
                best = (d, n1, n2)
        if best:
            rows.append((f["ref"], f["name"], best[0], best[1], best[2]))
    return sorted(rows, key=lambda r: r[2])


def edge_distances(pcb, top=5):
    x1, y1, x2, y2 = pcb["outline"]
    edge = Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]).exterior
    return sorted((it["shape"].distance(edge), it["name"], it["kind"]) for it in copper_items(pcb))[:top]


def _holes(pcb):
    holes = [(p["x"], p["y"], p["drill"], f"{f['ref']}.{p['number']}", "pad") for f in pcb["footprints"] for p in f["pads"] if p["drill"] > 0]
    holes += [(v["x"], v["y"], v["drill"], f"via{i}", "via") for i, v in enumerate(pcb["vias"])]
    return holes


def hole_spacing(pcb, top=4):
    """Smallest distance from one hole's edge to another hole's edge."""
    rows = [(math.hypot(a[0] - b[0], a[1] - b[1]) - (a[2] + b[2]) / 2, a[3], b[3]) for a, b in itertools.combinations(_holes(pcb), 2)]
    return sorted(rows)[:top]


def hole_to_track(pcb, top=4):
    """Hole edge to the edge of the nearest track of a different net (a track on the pad's own net is meant to touch it)."""
    rows = []
    for f in pcb["footprints"]:
        for p in f["pads"]:
            if p["drill"] <= 0:
                continue
            for i, s in enumerate(pcb["segments"]):
                if s["net"] == p["net"]:
                    continue
                d = LineString([(s["x1"], s["y1"]), (s["x2"], s["y2"])]).distance(Point(p["x"], p["y"])) - p["drill"] / 2 - s["width"] / 2
                rows.append((d, f"{f['ref']}.{p['number']}", f"track{i}", s["net"]))
    return sorted(rows)[:top]


def net_members(pcb, net):
    """What is on one net: ([pads as 'REF.pin'], number of track segments, number of vias). Shows, for instance, which parts a signal really passes through."""
    pads = [f"{f['ref']}.{p['number']}" for f in pcb["footprints"] for p in f["pads"] if p["net"] == net]
    return pads, sum(1 for s in pcb["segments"] if s["net"] == net), sum(1 for v in pcb["vias"] if v["net"] == net)
