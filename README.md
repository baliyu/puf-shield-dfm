# puf-shield-dfm

A self-directed manufacturing review of my own research PCB, the SRAM-PUF shield from my PhD testbed (KiCad 10, 2 layers, made by JLCPCB): a DFM review, a DFMEA, and a costed bill of materials with alternative parts.

Built with AI assistance (Claude). I supplied the design, the fabrication files, the photos, the order and what I remember of building it, and I decide what is true about the board; the tool, the tests and the write-ups were written with Claude.
This is a desk exercise on a research board. No manufacturer reviewed it, it is not industry experience, and the DFMEA scores are my judgement, not field data.

## Status

| Stage | What | State |
|---|---|---|
| 1 | Tool that reads the KiCad files, BOMs, manufacturing measurements ([FINDINGS_SO_FAR](docs/FINDINGS_SO_FAR.md)) | done |
| 2 | DFM review and a Rev B change list ([DFM_REVIEW](docs/DFM_REVIEW.md)) | done |
| 3 | DFMEA: 16 failure modes, each scored with the kind of evidence behind it ([DFMEA](docs/DFMEA.md)) | done |
| 4 | Costed BOM and alternative parts ([BOM](docs/BOM.md)) | partly done: 3 of 7 fitted lines priced |
| 5 | Results table and limits (this page) | done |

## Results

| Area | Result | Where |
|---|---|---|
| Is the file the board that was made? | All 63 holes in the PCB file match the fabrication drill files in position (within 0.003 mm) and diameter. Copper and silkscreen were not compared | FINDINGS_SO_FAR |
| Spacing and edges | Smallest gap between different nets 0.202 mm (the board's rule is 0.2, JLCPCB's minimum 0.10); copper to board edge 0.76 mm; no courtyard overlaps | FINDINGS_SO_FAR |
| The weak spot | Q1's footprint has 0.22 mm between pads and a 0.15 mm annular ring, below JLCPCB's stated absolute minimum of 0.18 mm for 2-layer 1 oz pads; this is where the hand-soldered bridge happened | DFM_REVIEW |
| Q1 replacement footprints | Staggered `TO-92`: ring 0.275 mm, fits in place, gap still 0.23 mm. `TO-92_Inline_Wide`: gap 1.04 mm and ring 0.35 mm, but it overlaps U2's socket. KiCad's `TO-92_HandSolder` is worse (0.17 mm gap, 0.175 mm ring) | DFM_REVIEW |
| Documentation | R1, R2 and C3 are not fitted but not marked do-not-populate; all six bottom silkscreen texts are under JLCPCB's size minimum | FINDINGS_SO_FAR |
| Design weakness | R1 is the only link between the host's gate pin and Q1's gate, so the design depends on an optional part | DFMEA D03 |
| DFMEA | 16 failure modes, 2 of them observed events (D01, D02). Highest numbers: poor joints 180, a smoke test that measures a node that cannot change 175, ESD 168, the Q1 bridge 147 | DFMEA |
| Alternatives | No equivalent for the 23K640 in this experiment. The BS170 is not a safe drop-in for the 2N7000: onsemi's BS170 is drain-gate-source, its 2N7000 source-gate-drain | BOM |
| Cost (partial) | SRAM, sockets and Q1 priced: 2.30 GBP per board at 1 board, 2.22 at 10, 1.91 at 100, ex VAT and ex delivery. The PCB cost 24.25 GBP including shipping for 5 boards (4.85 each at that size) | BOM |

## What surprised me

The staggered footprint fixed the ring but not the gap. KiCad's "HandSolder" footprint made both worse. The 2N7000's and BS170's leg orders differ by maker. And the smoke test I had used (SRAM pin 8 against board ground) could never have changed, because pin 8 is wired to 3.3 V.

## How it was checked

76 tests on invented fixtures, run in CI, plus a by-hand check where I broke the tool on purpose in 39 ways (wrong rotation, square corners, same-net items, drill axis flipped, costing breaks wrong, and so on); all 39 are caught.
Mistakes found along the way: my first pad model treated rounded corners as square and reported a false 0.099 mm gap (about 0.205 mm in fact); Python kept a stale compiled copy during my first break-it run and gave false passes; and I once wrote a reason for leaving R1 empty that I had not checked, and removed it.

## What is known and not known

From my notes of 28 August 2026: the first capture from the board was a valid, structurally sound one, the examiners asked only for the design, and one open issue was continuity at Q1. No Hamming distance was computed on the board, so this repository makes no claim about its PUF statistics.
How the host's gate pin reached Q1 on the board that ran captures, and why R2 was left off, are not recorded.

## Use

```
pip install -r requirements.txt
pytest -q
python -m pufdfm report --project path/to/kicad_project --gerbers path/to/fabrication_files
python -m pufdfm bom --project path/to/kicad_project --out bom.csv
python -m pufdfm footprint path/to/library/*.kicad_mod
python -m pufdfm net --project path/to/kicad_project /MOSFET_GATE
python -m pufdfm dfmea dfmea/puf_shield_dfmea.csv
python -m pufdfm cost bom/puf_shield_costed.csv --boards 1 10 100
```

The KiCad project and Gerber files are not in this repository (`hardware/` is ignored): the tool reads them from wherever you keep them.

## What is where

| Path | What it is |
|---|---|
| `pufdfm/sexp.py`, `kicad.py` | a reader for KiCad 10 text files (no KiCad install needed) |
| `pufdfm/checks.py`, `drill.py` | clearances, rings, pad gaps, hole spacing, net contents; hole comparison with the drill files |
| `pufdfm/bom.py`, `costing.py`, `dfmea.py` | the BOM, cost per board from price breaks (unpriced parts are listed, never counted as free), and the DFMEA table |
| `bom/`, `dfmea/` | the as-designed, as-built and costed BOMs, and the DFMEA data |
| `docs/` | findings, DFM review, DFMEA, costed BOM |
| `tests/` | 76 tests |

## Limits

One board, one design. The tool reads KiCad 10 text files and models pad shapes as circles, ovals, rectangles and rounded rectangles (others as their bounding rectangle). JLCPCB's limits are as retrieved on 1 November 2026 and change.
Two of the three prices are search snippets of distributor pages, not live reads, and four fitted lines are unpriced. The photo observations are not measurements. The library footprints I compared came from a public mirror in an older file format.
The DFMEA has no fault injection and no field data; its scores are mine.
