"""Layout checks for the generated Power BI report: every visual sits on the 1280x720 canvas and no two
visuals overlap (overlaps and off-canvas visuals were the cause of clipped/scrolling visuals)."""
from itertools import combinations

from fda_recall.pbip import pages

W, H = 1280, 720


def _boxes():
    for page, (_, visuals) in pages().items():
        for v in visuals:
            p = v["position"]
            yield page, v["name"], p["x"], p["y"], p["width"], p["height"]


def test_visuals_inside_canvas():
    for page, name, x, y, w, h in _boxes():
        assert x >= 0 and y >= 0 and x + w <= W and y + h <= H, f"{page}/{name} off canvas"


def test_no_overlapping_visuals():
    by_page: dict[str, list] = {}
    for b in _boxes():
        by_page.setdefault(b[0], []).append(b)
    for page, boxes in by_page.items():
        for a, b in combinations(boxes, 2):
            _, n1, x1, y1, w1, h1 = a
            _, n2, x2, y2, w2, h2 = b
            overlap = x1 < x2 + w2 and x2 < x1 + w1 and y1 < y2 + h2 and y2 < y1 + h1
            assert not overlap, f"{page}: {n1} overlaps {n2}"
