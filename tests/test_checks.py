import pytest

from fixtures import PCB
from pufdfm import checks, kicad


@pytest.fixture(scope="module")
def pcb():
    return kicad.parse_pcb(PCB)


def gap(pcb, a, b):
    items = {i["name"]: i for i in checks.copper_items(pcb)}
    return items[a]["shape"].distance(items[b]["shape"])


def test_a_track_passing_a_rounded_pad_corner_is_measured_against_the_rounded_corner(pcb):
    # measured on a real board: a square-cornered model gives 0.099 mm, the rounded corner about 0.205 mm
    assert gap(pcb, "R3.1", "track0") == pytest.approx(0.205, abs=0.01)


def test_the_same_pad_with_square_corners_would_be_much_closer(pcb):
    squared = {**pcb, "footprints": [dict(f, pads=[dict(p, rratio=0.0) for p in f["pads"]]) for f in pcb["footprints"]]}
    assert gap(squared, "R3.1", "track0") == pytest.approx(0.099, abs=0.01)


def test_clearances_skip_items_on_the_same_net_and_list_the_smallest_first(pcb):
    rows = checks.min_clearances(checks.copper_items(pcb), 50)
    assert rows == sorted(rows, key=lambda r: r[0])
    names = {(a, b) for _, a, b, _ in rows}
    assert ("J.1", "track1") not in names and ("track1", "J.1") not in names            # J.1 is GND and track1 is /SIG: different nets, may appear
    assert not any({"track1", "via0"} == {a, b} for a, b in names)                      # same net /SIG: never reported
    assert any({a, b} == {"R3.1", "track0"} for a, b in names)


def test_annular_ring_is_measured_on_the_narrow_side_of_the_pad(pcb):
    rings = {n: r for n, r, *_ in checks.annular_rings(pcb)}
    assert rings["Q1.1"] == pytest.approx(0.15) and rings["via0"] == pytest.approx(0.15) and rings["J.1"] == pytest.approx(0.35)
    assert checks.annular_rings(pcb)[0][1] <= checks.annular_rings(pcb)[-1][1]


def test_the_pad_gap_in_a_narrow_pitch_footprint_is_pitch_minus_pad_width(pcb):
    rows = {ref: d for ref, _, d, _, _ in checks.pad_gaps(pcb)}
    assert rows["Q1"] == pytest.approx(0.22, abs=0.001)          # 1.27 mm pitch, 1.05 mm wide pads
    assert rows["R3"] == pytest.approx(0.8, abs=0.01)


def test_hole_edge_to_hole_edge(pcb):
    d, a, b = checks.hole_spacing(pcb, 1)[0]
    assert d == pytest.approx(0.52, abs=0.001) and {a, b} <= {"Q1.1", "Q1.2", "Q1.3"}


def test_hole_to_track_ignores_a_track_on_the_pads_own_net(pcb):
    rows = checks.hole_to_track(pcb, 500)
    assert not any(h == "J.2" and t == "track1" for _, h, t, _ in rows)                 # J.2 is /SIG and so is track1
    assert any(h == "J.1" and t == "track1" for _, h, t, _ in rows)


def test_copper_to_board_edge(pcb):
    d, name, kind = checks.edge_distances(pcb, 1)[0]
    assert (name, kind) == ("via0", "via") and d == pytest.approx(0.7, abs=0.001)           # via at y=61, radius 0.3, outline at y=60
    edge = {n: d for d, n, _ in checks.edge_distances(pcb, 50)}
    assert edge["track1"] == pytest.approx(0.9, abs=0.001)                                    # track at y=61 with half width 0.1


def test_an_oval_pad_has_rounded_ends_not_square_corners():
    from shapely.geometry import Point
    pad = {"shape": "oval", "x": 0.0, "y": 0.0, "w": 1.0, "h": 2.0, "rot": 0.0}
    # (0.5, 1.0) is the corner of the 1 x 2 bounding box; the rounded end (radius 0.5, centred at y=0.5) is 0.207 mm away from it
    assert checks.pad_shape(pad).distance(Point(0.5, 1.0)) == pytest.approx(0.2071, abs=0.002)
    assert checks.pad_shape(pad).distance(Point(0.0, 1.0)) == pytest.approx(0.0, abs=0.001)


def test_a_rotated_pad_is_rotated_a_quarter_turn():
    pad = {"shape": "rect", "x": 0.0, "y": 0.0, "w": 2.0, "h": 1.0, "rot": 90.0}
    assert checks.pad_shape(pad).bounds == pytest.approx((-0.5, -1.0, 0.5, 1.0), abs=1e-9)


def test_copper_of_the_same_net_is_never_reported_but_other_nets_are():
    from shapely.geometry import box
    items = [{"name": "a", "net": "N1", "layers": {"F.Cu"}, "shape": box(0, 0, 1, 1)},
             {"name": "b", "net": "N1", "layers": {"F.Cu"}, "shape": box(1.1, 0, 2, 1)},
             {"name": "c", "net": "N2", "layers": {"F.Cu"}, "shape": box(0, 1.3, 1, 2)},
             {"name": "d", "net": "N3", "layers": {"B.Cu"}, "shape": box(0, 1.1, 1, 2)}]
    pairs = {frozenset((a, b)) for _, a, b, _ in checks.min_clearances(items, 10)}
    assert frozenset(("a", "b")) not in pairs                      # same net, 0.1 mm apart: meant to be connected
    assert frozenset(("a", "c")) in pairs                          # different nets, same layer
    assert not any("d" in p for p in pairs)                        # d is on the other side of the board
