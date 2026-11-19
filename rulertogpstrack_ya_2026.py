#!/usr/bin/env python3
"""
yandex_ruler_to_gpx.py

Convert a raw Yandex Maps ruler URL (the rl=... parameter) into a GPX track.

Usage:
    python yandex_ruler_to_gpx.py <link-file> [title]

<link-file> is a text file whose first non-empty line is a Yandex Maps URL.
If [title] is omitted, you will be prompted for one (as in the old Pascal tool).
"""

import sys
import urllib.parse
from pathlib import Path

DEFAULT_HEADER = """<?xml version="1.0" encoding="UTF-8"?>

<gpx xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0"
xmlns="http://www.topografix.com/GPX/1/0"
creator="Python 3"
xsi:schemaLocation="http://www.topografix.com/GPX/1/0
http://www.topografix.com/GPX/1/0/gpx.xsd">

<metadata>
    <name> Automatically Generated Track </name>
    <desc>- - - - - - - -</desc>
    <author> <name> Boris Zolotov </name>
        <link href="https://vk.com/boris.a.zolotov"> </link>
    </author>
    <link href="https://github.com/boris-a-zolotov"> </link>
    <keywords> gpx, python, route, bicycle </keywords>
</metadata>
"""

TAB = "    "


def parse_yandex_ruler(url: str) -> list[tuple[float, float]]:
    """Return a list of (lat, lon) tuples from a Yandex Maps ruler URL.

    Yandex rl= format:
        lon0,lat0~dlon1,dlat1~dlon2,dlat2~...
    The first point is absolute; the rest are deltas from the previous one.
    """
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    rl_values = params.get("rl")
    if not rl_values:
        raise ValueError("URL has no 'rl' (ruler) parameter")

    parts = rl_values[0].split("~")
    lon, lat = map(float, parts[0].split(","))
    points = [(lat, lon)]

    for part in parts[1:]:
        dlon, dlat = map(float, part.split(","))
        lon += dlon
        lat += dlat
        points.append((lat, lon))

    return points


def read_header() -> str:
    """Use in-hat.txt next to the script if present, else the embedded default."""
    hat = Path(__file__).resolve().parent / "in-hat.txt"
    if hat.is_file():
        return hat.read_text(encoding="utf-8")
    return DEFAULT_HEADER


def build_gpx(points: list[tuple[float, float]], title: str, header: str) -> str:
    out = [header.rstrip("\n"), "", ""]
    out.append(f"{TAB}<trk> <name>{title}</name>")
    out.append(f"{TAB}<desc>- - - - - - - -</desc> <trkseg>")
    for lat, lon in points:
        out.append(f'{TAB}{TAB}<trkpt lat="{lat:.8f}" lon="{lon:.8f}"> </trkpt>')
    out.append(f"{TAB}</trkseg> </trk>")
    out.append("</gpx>")
    return "\n".join(out) + "\n"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python yandex_ruler_to_gpx.py <link-file> [title]")
        sys.exit(1)

    link_path = Path(sys.argv[1])
    if not link_path.is_file():
        print(f"Error: file not found: {link_path}")
        sys.exit(1)

    title = sys.argv[2].strip() if len(sys.argv) > 2 else ""
    if not title:
        title = input("Insert title (Eng letters only): ").strip() or "track"

    url = next(
        (line.strip()
         for line in link_path.read_text(encoding="utf-8").splitlines()
         if line.strip()),
        "",
    )
    if not url:
        print("Error: link file is empty")
        sys.exit(1)

    try:
        points = parse_yandex_ruler(url)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    out_path = Path(f"{title}.gpx")
    out_path.write_text(build_gpx(points, title, read_header()), encoding="utf-8")
    print(f"Wrote {len(points)} points to {out_path.resolve()}")


if __name__ == "__main__":
    main()