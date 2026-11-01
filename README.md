# puf-shield-dfm

A self-directed manufacturing review of my own research PCB, the SRAM-PUF shield from my PhD testbed (KiCad 10, 2 layers, made by JLCPCB): a DFM review, a DFMEA, and a bill of materials with alternative parts and cost.

Built with AI assistance (Claude). I supplied the design, the fabrication files, the photos and the order, and I decide what is true about the board; the tool, the tests and the write-ups were written with Claude. This is a desk exercise on a research board.
No manufacturer reviewed it and it is not industry experience; the DFMEA scores will be my judgement, not field data.

## Status

| Stage | What | State |
|---|---|---|
| 1 | Tool that reads the KiCad files, as-designed and as-built BOM, manufacturing measurements, first findings | **done** ([docs/FINDINGS_SO_FAR.md](docs/FINDINGS_SO_FAR.md)) |
| 2 | DFM review document | not started |
| 3 | DFMEA built from the findings and from real events (a solder bridge at Q1, an unpopulated gate pull-down) | not started |
| 4 | Alternative parts (each checked against its datasheet) and cost at 1, 10 and 100 | not started |
| 5 | Results table and limits | not started |

## Use

```
pip install -r requirements.txt
pytest -q
python -m pufdfm report --project path/to/kicad_project --gerbers path/to/fabrication_files
python -m pufdfm bom --project path/to/kicad_project --out bom.csv
```

The KiCad project and Gerber files are not in this repository (`hardware/` is ignored): the tool reads them from wherever you keep them.

## What is where

| Path | What it is |
|---|---|
| `pufdfm/sexp.py`, `kicad.py` | a reader for KiCad 10 text files (no KiCad install needed) |
| `pufdfm/checks.py` | clearances, annular rings, pad gaps, hole spacing, edge distances |
| `pufdfm/drill.py` | compares the PCB's holes with the fabrication drill files |
| `pufdfm/bom.py` | the bill of materials from the schematic |
| `bom/` | `puf_shield_as_designed.csv` (from the schematic) and `puf_shield_as_built.csv` (what was actually fitted, with the evidence) |
| `docs/FINDINGS_SO_FAR.md` | the findings, how they were checked, and what is not done |
| `tests/` | 35 tests on invented fixtures, plus a deliberate-bug check run by hand |

## Limits

The tool reads KiCad 10 text files and was tested on one board. It models pad shapes as circles, ovals, rectangles and rounded rectangles; other pad shapes are treated as their bounding rectangle.
Its numbers are compared with JLCPCB's published limits as retrieved on 1 November 2026.
