# DFM review (stage 2)

Built with AI assistance (Claude). A self-directed review of my own research PCB, the SRAM-PUF shield (2 layers, JLCPCB, 5 boards ordered 3 Aug 2026). It is not a manufacturer review and not industry experience.
The measurements and how they were checked are in [FINDINGS_SO_FAR.md](FINDINGS_SO_FAR.md); this page turns them into a change list for a next revision ("Rev B") and says how each change would be verified.
JLCPCB limits are from their published capabilities page as retrieved on 1 November 2026.

## Change list for Rev B, in priority order

| # | Change | Why (measured) | How to verify before ordering |
|---|---|---|---|
| 1 | Replace Q1's footprint (`TO-92_Inline`: 0.22 mm pad gap, 0.15 mm ring, 0.52 mm hole gap) | Hand-soldering bridged this part, and its ring is below JLCPCB's stated 0.18 mm absolute minimum for 2-layer 1 oz pads. See the comparison below | `python -m pufdfm footprint` on the candidates; KiCad's own design-rule check; a 1:1 paper print with a spare 2N7000 |
| 2 | Mark R1, R2 and C3 as do-not-populate (or delete them) | They are not fitted, but the schematic lists them as fitted | Export the BOM again and compare it with `bom/puf_shield_as_built.csv` |
| 3 | Decide on R2, the gate pull-down: fit it, or write down why it is left off | Without it Q1's gate floats whenever the host pin is not driving it (reset, boot), so the SRAM supply state is undefined at those moments | Probe the gate with an oscilloscope across a host reset |
| 4 | Make all board silkscreen at least 1.0 mm high with 0.15 mm lines | Six bottom texts are 0.8 to 0.9 mm high with 0.12 to 0.14 mm lines, under JLCPCB's stated minimum | Re-run `python -m pufdfm report` (it counts texts under the limits) |
| 5 | Fix the BOM fields: part number and supplier per part, female header named as such, a "fitted" flag | The schematic names a male pin-header footprint for the female headers actually fitted, and carries no part numbers | The as-designed BOM equals the as-built BOM |
| 6 | Add two or three labelled test points (3V3, the switched ground, Q1's gate) | Q1's fault had to be found with continuity checks across closely spaced pins | Not measured; a suggestion |

## Q1: candidate footprints (KiCad library, measured with this tool)

| Footprint | Pad gap | Annular ring | Hole edge to hole edge | Pads | Fits where Q1 is? |
|---|---|---|---|---|---|
| `TO-92_Inline` (current) | 0.22 mm | 0.150 mm | 0.52 mm | 1.05 x 1.5, drill 0.75 | yes (it is there) |
| `TO-92` (staggered) | 0.23 mm | 0.275 mm | 1.05 mm | 1.3 x 1.3, drill 0.75 | yes, 1.73 mm from the nearest socket pad |
| `TO-92_Inline_Wide` | 1.04 mm | 0.350 mm | 1.74 mm | 1.5 x 1.5, drill 0.8 | **no**: it overlaps U2's socket pad, so it needs a re-layout |
| `TO-92_Wide` | 1.78 mm | 0.350 mm | 2.79 mm | 1.5 x 1.5, drill 0.8 | not tried (wider than the inline-wide one) |
| `TO-92_HandSolder` | 0.17 mm | 0.175 mm | 1.05 mm | 1.1 x 1.8, drill 0.75 | not tried: **worse** than the current one on gap and ring |

What this says: the staggered `TO-92` fixes the annular ring and the hole spacing in place, but not the 0.23 mm copper gap, so the bridge risk stays. The wide inline version fixes the gap (1.04 mm) and the ring, but the 2N7000's leads
(1.27 mm apart) have to be spread to fit 2.54 mm pads, and it needs about 3 mm of board that U2's socket now uses. The "HandSolder" variant has longer pads for easier iron access, but its gaps are smaller, so it does not help against bridging.
The library copy I measured is the public mirror on GitHub, which uses an older file format; its numbers for `TO-92_Inline` match the footprint on the board, but check the candidates in the library that ships with KiCad 10 before choosing.

## Review by area

**Fabrication (JLCPCB).** Passes: smallest gap between different nets 0.202 mm (limit 0.10 mm), copper to board edge 0.76 mm (0.2 mm), plated hole edge to track 0.40 mm (0.28 mm, 0.35 recommended), via pad 0.6 mm on a 0.3 mm hole,
board 50.8 x 24.5 mm as ordered, hole pattern identical to the drill files. Does not pass or is marginal: Q1's annular ring (above), hole spacing at Q1 (0.52 mm against a 0.45 mm minimum), silkscreen size. Not checked: solder mask openings, silkscreen to pad distance, the copper layers against the Gerbers.

**Assembly (by hand).** The geometry that hurts hand soldering is Q1's 1.27 mm pitch. The photos of the assembled board show heavy, balled solder, burnt flux residue near U1 and Q1, a crooked J1B1 and a bent-over Q1. These are observations from photos, not measurements,
and a PCB change cannot fix technique; they are worth a short written assembly note (order of fitting, solder amount, flux cleaning, a look under magnification) in a next revision.

**Test and debug.** There are no test points and no ground plane; every probe point is a component pin. Fine for a research rig, slow for fault-finding.

**Documentation and BOM.** The schematic's BOM disagrees with the board in four ways (items 2 and 5 above, plus the unconfirmed R2). The as-built BOM with evidence is in `bom/`.

## What this review did not do

No DFM review by a manufacturer, no assembly process data, no yield figures, no thermal or electrical analysis, and no check of the copper layers against the Gerbers. The DFMEA (stage 3) will cover failure modes and effects; its scores will be my judgement.
