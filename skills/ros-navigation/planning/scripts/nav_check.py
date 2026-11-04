"""nav_check (LOCAL lib): numpy-only oriented footprint stamp.

cv2-free equivalent of the library footprint_clips_grid (local env
has no cv2): tests rotated-rect corners + edge midpoints against
occupied cells AND occupied-cell centers against the rect. Either
hit = clip. Conservative on clear-cut cases; see N3 gates.
"""
import math
import numpy as np


def footprint_clips_np(x, y, yaw, size, res, grid, xr, yr):
    hw, hh = size[0] / 2.0, size[1] / 2.0
    c, s = math.cos(yaw), math.sin(yaw)
    corners = [(hw, hh), (hw, -hh), (-hw, hh), (-hw, -hh),
               (hw, 0), (-hw, 0), (0, hh), (0, -hh)]
    pts = [(x + dx * c - dy * s, y + dx * s + dy * c)
           for dx, dy in corners]
    H, W = grid.shape

    def _occ(px, py):
        cx = int((px - xr[0]) / res)
        cy = int((py - yr[0]) / res)
        return (0 <= cx < W and 0 <= cy < H and grid[cy, cx] > 0)

    if any(_occ(px, py) for px, py in pts):
        return True
    # occupied centers inside the rect (catches straddles)
    reach = math.hypot(hw, hh)
    x0 = int((x - reach - xr[0]) / res)
    x1 = int((x + reach - xr[0]) / res) + 1
    y0 = int((y - reach - yr[0]) / res)
    y1 = int((y + reach - yr[0]) / res) + 1
    for cy in range(max(0, y0), min(H, y1)):
        for cx in range(max(0, x0), min(W, x1)):
            if grid[cy, cx] == 0:
                continue
            wx = xr[0] + (cx + 0.5) * res
            wy = yr[0] + (cy + 0.5) * res
            lx = (wx - x) * c + (wy - y) * s
            ly = -(wx - x) * s + (wy - y) * c
            if abs(lx) <= hw and abs(ly) <= hh:
                return True
    return False
