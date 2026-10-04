#!/usr/bin/env python3
"""Generate a cat-walking animation SVG from GitHub contributions.

The cat walks a snake-like path across the contribution grid,
"eating" the green squares as it goes.
Outputs: dist/github-contribution-grid-cat.svg
"""
import re
import urllib.request

USER = "pradaxc"
CELL = 12
GAP = 4
PITCH = CELL + GAP

CAT = "\U0001f408"  # 🐈


def fetch_contributions(user):
    url = f"https://github.com/users/{user}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_grid(html):
    # <td ...><tool-tip ...>N contributions on DATE</tool-tip></td> or rect-based
    # Newer format: <td data-date="..." data-level="0-4" ...>
    cells = re.findall(
        r'data-date="([^"]+)"[^>]*data-level="(\d)"', html)
    if not cells:
        # fallback: rect elements
        cells = re.findall(
            r'<rect[^>]*data-date="([^"]+)"[^>]*data-level="(\d)"', html)
    return cells  # list of (date, level) in column-major order


def level_color(level):
    return ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"][int(level)]


def build_path(ncols, nrows=7):
    """Snake path through the grid (boustrophedon)."""
    path = []
    for col in range(ncols):
        rows = range(nrows) if col % 2 == 0 else range(nrows - 1, -1, -1)
        for row in rows:
            path.append((col, row))
    return path


def main():
    html = fetch_contributions(USER)
    cells = parse_grid(html)
    if not cells:
        raise SystemExit("could not parse contribution grid")
    ncols = (len(cells) + 6) // 7
    # pad to full columns
    while len(cells) < ncols * 7:
        cells.append((None, "0"))

    path = build_path(ncols)
    W = ncols * PITCH + GAP
    H = 7 * PITCH + GAP + 30  # extra space for cat

    # Build frames: cat moves along path, squares "eaten" (fade) as it passes
    nframes = len(path)
    # To keep file small, sample every Nth frame
    step = max(1, nframes // 60)
    frames = list(range(0, nframes, step))
    if frames[-1] != nframes - 1:
        frames.append(nframes - 1)

    dur = 0.12  # seconds per frame
    total_dur = len(frames) * dur

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
               f'viewBox="0 0 {W} {H}">')
    out.append('<style>.cell{shape-rendering:crispEdges}</style>')

    # Static grid (all cells, dimmed as "uneaten" initially)
    for idx, (date, level) in enumerate(cells):
        col, row = idx // 7, idx % 7
        x, y = GAP + col * PITCH, GAP + row * PITCH
        color = level_color(level)
        out.append(f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" '
                   f'height="{CELL}" rx="2" fill="{color}" opacity="0.35" '
                   f'id="c{idx}"/>')

    # Eaten cells light up as the cat passes (animate opacity)
    for fi, pi in enumerate(frames):
        t0 = fi * dur
        for j in range(max(0, pi - 8), pi + 1):
            idx = j  # path index == cell index (boustrophedon matches column-major)
            if idx < len(cells):
                out.append(
                    f'<animate xlink:href="#c{idx}" attributeName="opacity" '
                    f'from="0.35" to="1" dur="0.01s" begin="{t0:.2f}s" '
                    f'fill="freeze" xmlns:xlink="http://www.w3.org/1999/xlink"/>')

    # Cat: text emoji moving along path
    # Build animateMotion with keyPoints
    pts = []
    for pi in frames:
        col, row = path[pi]
        x = GAP + col * PITCH + CELL / 2
        y = GAP + row * PITCH + CELL / 2
        pts.append(f"{x},{y}")
    path_d = "M" + " L".join(pts)

    out.append(f'<path id="catpath" d="{path_d}" fill="none" stroke="none"/>')
    out.append(
        f'<text font-size="16" text-anchor="middle" dominant-baseline="central">'
        f'<textPath xlink:href="#catpath" xmlns:xlink="http://www.w3.org/1999/xlink">'
        f'<animate attributeName="startOffset" from="0%" to="100%" '
        f'dur="{total_dur:.1f}s" repeatCount="indefinite"/>'
        f'{CAT}</textPath></text>')

    out.append('</svg>')

    import os
    os.makedirs("dist", exist_ok=True)
    with open("dist/github-contribution-grid-cat.svg", "w") as f:
        f.write("\n".join(out))
    print(f"wrote cat svg: {W}x{H}, {len(frames)} frames, {ncols} cols")


if __name__ == "__main__":
    main()
