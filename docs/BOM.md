# Costed BOM and alternative parts (stage 4, partly done)

Built with AI assistance (Claude). A self-directed exercise on my own research board; prices are what the pages showed on the day, not quotes.
Status: **3 of the 7 fitted lines are priced.** The totals below are therefore partial, and they will rise when the rest is priced. Nothing unpriced is counted as free: `python -m pufdfm cost bom/puf_shield_costed.csv` lists those lines every time.

## What is priced, and how far to trust it

| Line | Price (GBP, ex VAT) at 1 / 10 / 100 boards | Source | Confidence |
|---|---|---|---|
| U1, U2: 23K640-I/P, 2 per board | 0.61 / 0.61 / 0.5753 each | DigiKey UK product page, read 1 Nov 2026 | live page |
| U1, U2 sockets: DIP-8 turned pin (CPC SC15361), 2 per board | 0.44 / 0.44 / 0.34 each | CPC search snippet; the one-off price was not shown, so the 10-off price stands in | search snippet |
| Q1: 2N7000 (Diotec), 1 per board | 0.20 / 0.123 / 0.0765 | DigiKey UK search snippet | search snippet |

Priced fitted lines, per board: **2.30 GBP at 1 board, 2.22 at 10, 1.91 at 100.** Not yet priced: C1 and C2 (100 nF 0805), R3 (4.7 kOhm 0805), J1A1 and J1B1 (female headers) and the bare PCB. The order file records 24.25 for 5 boards but not the currency or whether it includes shipping, so I have not turned it into a per-board price.
A price break is chosen from the number of parts ordered (parts per board times boards), which is why the SRAM stays at 0.61 for 10 boards: 20 chips is still below the 25-off break.

Two things the page itself shows that matter more than the pennies: DigiKey UK charges 22 GBP delivery on orders under 65 GBP, which is several times the priced parts for a single board, so a build should be ordered in one basket; and the lead time on the SRAM page was 5 weeks when read, while older cached copies of the same page showed 9 to 36 weeks, so it moves.

## Alternative parts: what was checked

| Part | Result | Evidence |
|---|---|---|
| 23K640-I/P (SRAM) | **No equivalent for this experiment**: a different chip is a different PUF, so any swap restarts the characterisation. The 23A640 has the same pinout but runs at 1.5 to 1.95 V, so it does not belong on a 3.3 V board. The 23K640-E/P (automotive temperature) is listed as a similar substitute | Microchip DS22126E (device table, pin table); DigiKey UK page |
| 23K640 in SOIC (SN) or TSSOP (ST) | Same pin numbering as the PDIP part, but a different footprint; the shield has DIP sockets | Microchip DS22126E, package types |
| Q1: 2N7000 | The leg order depends on the datasheet. onsemi's 2N7000 is source-gate-drain (pin 1 source). onsemi's BS170 is drain-gate-source, the reverse; some other makers' BS170 are source-gate-drain. So the BS170 is **not** a safe drop-in. A third-party page reports that onsemi's January 2022 2N7000 datasheet printed the 2N7000 pinout swapped and that onsemi's support called it an error; I have not verified that, so confirm with a meter | onsemi 2N7000/D (style 22) and BS170/D (style 30); Siemens and Philips BS170 datasheets (source-gate-drain); etechnophiles.com on the 2022 datasheet |
| Q1 as an SMD part (2N7002) | Not tried: a different package, so not a drop-in on this footprint | not checked |
| C1, C2, R3 (0805), sockets, headers | Alternatives not checked yet | not done |

## Not done yet

Prices for C1, C2, R3, the headers and the PCB; alternatives for the passives, sockets and headers; the maker of the 2N7000 actually fitted (so the leg-order check is against the right datasheet); supply-risk notes for the rest; a delivery-inclusive cost for a one-off build.
