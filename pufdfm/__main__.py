"""python -m pufdfm report --project DIR [--gerbers DIR]   prints the manufacturing measurements for a KiCad project
   python -m pufdfm bom --project DIR [--out FILE]          writes the as-designed bill of materials as CSV
   python -m pufdfm dfmea FILE [--markdown]                  checks a DFMEA table and prints it ranked by risk priority number
   python -m pufdfm net --project DIR NAME...                which pads, tracks and vias are on a net
   python -m pufdfm footprint FILE...                       pad gap, annular ring and hole spacing of library footprints (.kicad_mod)"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import bom, checks, dfmea, drill, kicad


def _one(directory, pattern):
    hits = sorted(Path(directory).glob(pattern))
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one {pattern} in {directory}, found {len(hits)}")
    return hits[0]


def cmd_bom(args):
    parts, meta = kicad.load_schematic(_one(args.project, "*.kicad_sch"))
    text = bom.to_csv(bom.group(parts), ["refs", "qty", "value", "footprint", "dnp"])
    if args.out:
        Path(args.out).write_text(text, newline="\n")
        print(f"wrote {args.out}")
    else:
        print(text, end="")
    return 0


def cmd_report(args):
    parts, meta = kicad.load_schematic(_one(args.project, "*.kicad_sch"))
    pcb = kicad.load_pcb(_one(args.project, "*.kicad_pcb"))
    print(f"{meta.get('title', '?')}, rev {meta.get('rev', '?')}: {len(parts)} parts in the schematic, {len(pcb['footprints'])} footprints, "
          f"{len(pcb['segments'])} track segments, {len(pcb['vias'])} vias, {pcb['zones']} copper zones")
    flagged = [p["ref"] for p in parts if p["dnp"]]
    print(f"parts marked do-not-populate in the schematic: {', '.join(flagged) if flagged else 'none'}")
    if args.gerbers:
        files = sorted(Path(args.gerbers).rglob("*.drl"))
        holes = [h for f in files for h in drill.read_drill(f.read_text())]
        missing, extra = drill.compare(pcb, holes)
        print(f"\nholes: PCB file {len(drill.pcb_holes(pcb))}, drill files {len(holes)} ({', '.join(f.name for f in files)})")
        print("  PCB holes missing from the drill files:", missing or "none")
        print("  drill-file holes missing from the PCB:", extra or "none")
    items = checks.copper_items(pcb)
    print("\nsmallest copper gaps between different nets (mm):")
    for d, a, b, layers in checks.min_clearances(items, 3):
        print(f"  {d:.3f}  {a} - {b} {layers}")
    print("smallest gap between two pads of one footprint (mm):")
    for ref, name, d, n1, n2 in checks.pad_gaps(pcb)[:3]:
        print(f"  {d:.3f}  {ref} pads {n1}-{n2} ({name})")
    print("smallest annular rings (mm):")
    for name, ring, w, h, dr in checks.annular_rings(pcb)[:4]:
        print(f"  {ring:.3f}  {name} pad {w}x{h} drill {dr}")
    print("hole edge to hole edge (mm):", ", ".join(f"{d:.3f} {a}-{b}" for d, a, b in checks.hole_spacing(pcb, 2)))
    print("hole edge to track of another net (mm):", ", ".join(f"{d:.3f} {a}-{t}" for d, a, t, n in checks.hole_to_track(pcb, 2)))
    if pcb["outline"]:
        print("copper to board edge (mm):", ", ".join(f"{d:.3f} {n}" for d, n, k in checks.edge_distances(pcb, 2)))
    small = [t for t in pcb["texts"] if (t["height"] or 9) < 1.0 or (t["thickness"] or 9) < 0.15]
    print(f"silkscreen text below 1.0 mm height or 0.15 mm line width: {len(small)} of {len(pcb['texts'])}")
    return 0


def cmd_dfmea(args):
    rows = dfmea.load(Path(args.file).read_text(encoding="utf-8"))
    problems = dfmea.validate(rows)
    if problems:
        print("\n".join(problems))
        return 1
    if args.markdown:
        print(dfmea.to_markdown(rows), end="")
        return 0
    print(f"{len(rows)} failure modes, ranked by RPN (severity x occurrence x detection):")
    for r in dfmea.ranked(rows):
        print(f"  {dfmea.rpn(r):4d}  S{r['severity']} O{r['occurrence']} D{r['detection']}  {r['id']}  {r['failure_mode']}  [{r['evidence_type']}]")
    return 0


def cmd_net(args):
    pcb = kicad.load_pcb(_one(args.project, "*.kicad_pcb"))
    for name in args.names:
        pads, tracks, vias = checks.net_members(pcb, name)
        print(f"{name}: pads {', '.join(pads) if pads else 'none'}; {tracks} track segments; {vias} vias")
    return 0


def cmd_footprint(args):
    print(f"{'footprint':36s} pads  pad gap  ring  hole gap  pad size       drill")
    for path in args.files:
        fp = kicad.parse_pcb("(kicad_pcb " + Path(path).read_text(encoding="utf-8") + ")")
        for f in fp["footprints"]:
            if len(f["pads"]) < 2:
                continue
            gap = checks.pad_gaps(fp)[0][2]
            rings = checks.annular_rings(fp)
            hole = checks.hole_spacing(fp, 1)
            p0 = f["pads"][0]
            print(f"{f['name']:36s} {len(f['pads']):4d}  {gap:7.2f}  {rings[0][1] if rings else float('nan'):4.3f}  "
                  f"{hole[0][0] if hole else float('nan'):8.2f}  {p0['w']}x{p0['h']:<8}  {p0['drill']}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pufdfm", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--project", required=True)
    r.add_argument("--gerbers")
    r.set_defaults(fn=cmd_report)
    b = sub.add_parser("bom")
    b.add_argument("--project", required=True)
    b.add_argument("--out")
    b.set_defaults(fn=cmd_bom)
    d = sub.add_parser("dfmea")
    d.add_argument("file")
    d.add_argument("--markdown", action="store_true")
    d.set_defaults(fn=cmd_dfmea)
    n = sub.add_parser("net")
    n.add_argument("--project", required=True)
    n.add_argument("names", nargs="+")
    n.set_defaults(fn=cmd_net)
    fpc = sub.add_parser("footprint")
    fpc.add_argument("files", nargs="+")
    fpc.set_defaults(fn=cmd_footprint)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
