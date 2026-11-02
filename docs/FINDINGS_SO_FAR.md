# Findings so far (stage 1)

Built with AI assistance (Claude). This is a self-directed review of my own research PCB, the SRAM-PUF shield I designed for my PhD testbed. It is a desk exercise: no manufacturer reviewed it, the DFMEA scores
(stage 3) will be my judgement and not field data, and nothing here is industry experience. Status: **stage 1 of 5, measurements only**. The DFMEA and the costed bill of materials are not written yet.

## What was analysed

| Input | What it is |
|---|---|
| `puf_shield.kicad_sch`, `.kicad_pcb`, `.kicad_pro` | KiCad 10 project, saved as a backup on 29 Aug 2026 (schematic 30 Jul, drill file 31 Jul) |
| `pufshield_Y2.zip` | the Gerber and drill package JLCPCB made from my order of 3 Aug 2026, with JLCPCB's check files |
| JLCPCB order specification | 2-layer FR-4, 1.6 mm, 1 oz, HASL (leaded), green mask, white silkscreen, 50.8 x 24.5 mm, 5 boards |
| 4 photos | bare board top and bottom, assembled board top and bottom |
| JLCPCB's published capabilities | https://jlcpcb.com/capabilities/pcb-capabilities (page retrieved 1 Nov 2026; limits change, so re-check before relying on them) |

The tool in `pufdfm/` reads the KiCad text files directly. `python -m pufdfm report --project <dir> --gerbers <dir>` reproduces every number below.

## How the measurements were checked

- **The geometry code was tested against the real board.** All 63 holes in the PCB file match the 63 holes in the fabrication drill files in position (within 0.003 mm) and diameter. That also shows the hole pattern is the one that was made.
  It does not cover copper, silkscreen or solder mask, and the PCB file was saved after the order, so tracks could have changed; I have not compared the copper layers with the Gerbers.
- **My first pass was wrong, and I caught it.** It reported a track 0.099 mm from R3's pad, below the board's own 0.2 mm rule. The cause was my pad model: it treated the 0805 pads' rounded corners as square. With the rounded corners
  the gap is about 0.205 mm. A test now pins that case (`test_checks.py`).
- 76 tests pass. I also broke the tool on purpose in 39 ways (wrong rotation, square corners, same-net items, annular ring on the wrong side, drill axis flipped, BOM merging do-not-populate parts, and so on) and all 39 are caught.
  The first run of that check was unreliable because Python kept a stale compiled copy of a file; I found it, switched the cache off for the check, and four gaps in my tests turned up and were closed.

## Findings

Severity is my judgement: **A** worth changing in a next revision, **B** minor or a documentation fix, **C** passed.

| # | Finding | Evidence | Limit it is compared with | Sev |
|---|---|---|---|---|
| 1 | R1, R2 and C3 are not fitted on the board but are not marked do-not-populate in the schematic, so a BOM exported from the schematic lists them as fitted | photos show empty pads; schematic flags are all "no"; `bom/` | none (BOM hygiene) | A |
| 2 | Q1's footprint (TO-92 inline, 1.27 mm pitch) leaves **0.22 mm** between pads, which is where a hand-soldered bridge happens | pads 1.05 x 1.5 mm at 1.27 mm pitch | JLCPCB's solder mask bridge minimum is 0.10 mm, so the board can be made; hand soldering is what suffers | A |
| 3 | Q1's pads have only **0.15 mm** annular ring on the narrow side (pad 1.05 mm, drill 0.75 mm) | computed from the footprint | JLCPCB, 2-layer 1 oz plated through-hole pads: recommended 0.25 mm, absolute minimum 0.18 mm. The boards were made and JLCPCB's check files show no flag, but I cannot interpret those fields | A |
| 4 | Hole edge to hole edge at Q1 is 0.52 mm | computed | JLCPCB pad hole-to-hole minimum 0.45 mm (passes, with 0.07 mm to spare) | B |
| 5 | All six silkscreen texts on the bottom side are below JLCPCB's limits: four at 0.8 mm height and 0.12 mm line width, two at 0.9 mm and 0.14 mm | KiCad text settings | minimum height 1.0 mm, line width 0.15 mm. The text printed legibly in the photos | B |
| 6 | The fitted J1A1 and J1B1 are female headers, but the schematic footprint is the male pin-header pattern | photos; schematic | documentation only; same hole pattern | B |
| 7 | No copper zones: no ground plane or pour, all 145 track segments are 0.2 mm | `zones = 0`; track widths | fabricable; worth noting for a board whose thesis found ground-plane geometry mattered | B |
| 8 | The surface finish ordered is leaded HASL | order specification | fine for a research board; a product would need lead-free HASL or ENIG | B |
| 9 | R2 (the 100 kOhm gate pull-down) is left off, so Q1's gate floats whenever the host pin is not driving it (reset, boot) | schematic nets `/GATE_DRV`; photos | design decision to confirm; carried into the DFMEA | A, to confirm |
| 14 | R1 is the only connection between the host's gate-drive pin and Q1's gate, and the build plan left it empty, so Q1 would be undriven unless a wire or solder link was added | `pufdfm net`: the host gate net is on J2.8, J1B1.10 and R1.1 only; Q1's gate net is on Q1.2, R1.2 and R2.1 only; photo: R1 pads empty; the August notes show the host pin toggling while Q1's gate did not | none (design analysis); the builder states the shield worked as intended, so the working board must have had the gate linked; the photographed board may not be that one | A, as a design weakness |
| 10 | Spacing: the smallest gap between copper of different nets is **0.202 mm** | computed with rounded pad corners | project rule 0.2 mm; JLCPCB 0.10 mm | C |
| 11 | Copper to board edge 0.762 mm (via) | computed | project rule 0.5 mm; JLCPCB 0.2 mm | C |
| 12 | Plated hole edge to a track of another net 0.400 mm | computed | JLCPCB minimum 0.28 mm, recommended 0.35 mm | C |
| 13 | Vias 0.6 mm pad, 0.3 mm drill; no courtyard overlaps; outline 50.8 x 24.5 mm as ordered | computed | JLCPCB: via pad at least 0.1 mm larger than the hole | C |

### Observations from the photos (not measured, to confirm in person)

- The bottom side has heavy solder on the header and socket joints, several balled rather than filleted, and dark burnt flux residue near the U1 pins and Q1.
- J1B1 sits crooked with melted plastic at one end; Q1 appears to be seated bent over rather than upright, close to the U2 socket.
- C1 and C2 are fitted; R1, R2, C3, J2 and J3 are empty.

## Not done yet

DFMEA (stage 3); alternative parts and a costed bill of materials (stage 4); a comparison of the copper and silkscreen layers with the Gerbers; solder-mask and silkscreen-to-pad clearances; and confirming that the 29 Aug file is the version that was ordered.

## Unknown, and recorded as unknown

1. How the host's gate pin reached Q1's gate on the board that ran captures (R1 fitted, or a link added): the builder does not remember and the notes do not say.
2. Why R2 was left off: not remembered.
3. Whether the shield worked: the builder states it worked as intended; the notes reviewed end on 24 Aug 2026 with the fault unresolved, so I have not verified it.
4. Whether the tracks changed after the 3 Aug order.
5. The PCB order: 24.25 GBP including shipping for 5 boards, per the builder (4.85 per board at that order size).
