"""Reads a KiCad 10 project's text files (schematic and PCB) with no KiCad install."""
from __future__ import annotations

import math

from .sexp import find, find_all, parse, prop


def _f(x):
    return float(x)


def _natural(ref):
    i = len(ref)
    while i > 0 and ref[i - 1].isdigit():
        i -= 1
    head = ref[:i]
    return (head, int(ref[i:]) if ref[i:] else 0, ref)


def parse_schematic(text):
    sch = parse(text)
    parts = []
    for s in [c for c in sch if isinstance(c, list) and c and c[0] == "symbol"]:
        ref = prop(s, "Reference")
        if not ref or ref.startswith("#"):                       # power symbols and flags are not parts
            continue
        flag = lambda k: (find(s, k) or [None, None])[1]
        parts.append({"ref": ref, "value": prop(s, "Value"), "lib_id": find(s, "lib_id")[1], "footprint": prop(s, "Footprint") or "",
                      "dnp": flag("dnp") == "yes", "in_bom": flag("in_bom") != "no", "on_board": flag("on_board") != "no"})
    title = find(sch, "title_block") or []
    meta = {c[0]: c[1] for c in title if isinstance(c, list) and len(c) > 1 and c[0] in ("title", "rev", "company")}
    return sorted(parts, key=lambda p: _natural(p["ref"])), meta


def rotate_point(px, py, deg):
    """A footprint's rotation as KiCad stores it: degrees counter-clockwise on screen, y pointing down."""
    a = math.radians(deg)
    return px * math.cos(a) + py * math.sin(a), -px * math.sin(a) + py * math.cos(a)


def parse_pcb(text):
    pcb = parse(text)
    fps = []
    for f in find_all(pcb, "footprint") + find_all(pcb, "module"):      # "module" is the older name KiCad used before version 6
        at = find(f, "at") or ["at", "0", "0"]                   # a footprint from a library file has no position: it sits at the origin
        x, y = _f(at[1]), _f(at[2])
        rot = _f(at[3]) if len(at) > 3 else 0.0
        pads = []
        for p in find_all(f, "pad"):
            pat = find(p, "at")
            rx, ry = rotate_point(_f(pat[1]), _f(pat[2]), rot)
            size, drill, net = find(p, "size"), find(p, "drill"), find(p, "net")
            rr = find(p, "roundrect_rratio")
            drill_d = 0.0
            if drill:
                nums = [_f(v) for v in drill[1:] if isinstance(v, str) and v != "oval"]          # skips a nested (offset ...) entry
                drill_d = nums[0] if nums else 0.0
            pads.append({"number": str(p[1]), "type": p[2], "shape": p[3], "x": x + rx, "y": y + ry,
                         "rot": (rot + (_f(pat[3]) if len(pat) > 3 else 0.0)) % 360, "w": _f(size[1]), "h": _f(size[2]), "drill": drill_d,
                         "layers": [str(l) for l in find(p, "layers")[1:]], "net": str(net[1]) if net else "", "rratio": _f(rr[1]) if rr else 0.0})
        fps.append({"ref": prop(f, "Reference") or "REF**", "name": str(f[1]), "layer": str(find(f, "layer")[1]), "x": x, "y": y, "rot": rot, "pads": pads})
    segs = [{"x1": _f(find(s, "start")[1]), "y1": _f(find(s, "start")[2]), "x2": _f(find(s, "end")[1]), "y2": _f(find(s, "end")[2]),
             "width": _f(find(s, "width")[1]), "layer": str(find(s, "layer")[1]), "net": str(find(s, "net")[1])} for s in find_all(pcb, "segment")]
    vias = [{"x": _f(find(v, "at")[1]), "y": _f(find(v, "at")[2]), "size": _f(find(v, "size")[1]), "drill": _f(find(v, "drill")[1]),
             "net": str(find(v, "net")[1])} for v in find_all(pcb, "via")]
    outline = None
    for r in find_all(pcb, "gr_rect"):
        if str(find(r, "layer")[1]) == "Edge.Cuts":
            s, e = find(r, "start"), find(r, "end")
            outline = (_f(s[1]), _f(s[2]), _f(e[1]), _f(e[2]))
    texts = []
    for t in find_all(pcb, "gr_text"):
        fnt = find(find(t, "effects") or [], "font") or []
        sz, th = find(fnt, "size"), find(fnt, "thickness")
        texts.append({"text": str(t[1]), "layer": str(find(t, "layer")[1]), "height": _f(sz[2]) if sz else None, "thickness": _f(th[1]) if th else None})
    return {"footprints": fps, "segments": segs, "vias": vias, "outline": outline, "texts": texts, "zones": len(find_all(pcb, "zone"))}


def load_schematic(path):
    return parse_schematic(open(path, encoding="utf-8").read())


def load_pcb(path):
    return parse_pcb(open(path, encoding="utf-8").read())
