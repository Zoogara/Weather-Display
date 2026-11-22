#!/usr/bin/env python3
"""Make the radar base maps (radar_base_z5.png, radar_base_z6.png, radar_base_z7.png).

Each base map is the 380x330 window of the radar panel, drawn from Esri World Street Map tiles at the same
centre and scale as the matching Rainviewer radar frame, with a marker at the centre:

    Rainviewer 512px frame at zoom Z  ==  Esri 256px tiles at zoom Z+1

The display shows 384px frames scaled 4/3, which is the same as 512px frames, so the maps line up with the radar.

Town names come from OpenStreetMap (Overpass API) and are drawn in the repo's calibri font, biggest places first,
skipping any name that would overlap one already placed.

Usage:   python3 tools/make_radar_base.py LATITUDE LONGITUDE [--out DIR] [--zooms 5 6 7]
Needs:   Pillow (pip install pillow).  Tiles are cached in ~/.cache/weather-display-tiles.
Note:    Esri's map tiles and OpenStreetMap data have their own terms of use; these maps are for personal use.
"""
import argparse, json, math, os, subprocess, time
from PIL import Image, ImageDraw, ImageFont

WIN_W, WIN_H = 380, 330          # radar panel window (see packages/weather-lcd7/radar.yaml)
FRAME = 512                      # radar frame size as shown (384px scaled 4/3)
TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
CACHE = os.path.expanduser("~/.cache/weather-display-tiles")


def tile(z, x, y):
    path = os.path.join(CACHE, f"{z}_{x}_{y}.jpg")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        # curl rather than urllib: python.org builds of Python on macOS often have no CA certificates installed
        subprocess.run(["curl", "-fsS", "-m", "30", "-A", "weather-display-basemap/1.0", "-o", path + ".tmp",
                        TILE_URL.format(z=z, x=x, y=y)], check=True)
        os.replace(path + ".tmp", path)
    return Image.open(path).convert("RGB")


def render(lat, lon, tile_zoom, size):
    """size x size picture centred on lat/lon from 256px tiles at tile_zoom."""
    world = 256 * 2 ** tile_zoom
    cx = (lon + 180.0) / 360.0 * world
    s = math.sin(math.radians(lat))
    cy = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * world
    left, top = cx - size / 2, cy - size / 2
    out = Image.new("RGB", (size, size))
    for ty in range(int(top // 256), int((top + size - 1) // 256) + 1):
        for tx in range(int(left // 256), int((left + size - 1) // 256) + 1):
            out.paste(tile(tile_zoom, tx, ty), (round(tx * 256 - left), round(ty * 256 - top)))
    return out


LABELS_MAX = {5: 7, 6: 16, 7: 22}   # how many town names to try per zoom level


def px_to_latlon(px, py, world):
    lon = px / world * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / world))))
    return lat, lon


def latlon_to_px(lat, lon, world):
    x = (lon + 180.0) / 360.0 * world
    s = math.sin(math.radians(lat))
    return x, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * world


def towns(lat, lon, tile_zoom, ox, oy):
    """Cities and towns inside the window: [(name, rank, x, y)] with x, y in window pixels."""
    world = 256 * 2 ** tile_zoom
    # the window is 380x330 at 512px-frame scale = 256px tiles at tile_zoom, so frame pixels == world pixels
    cx, cy = latlon_to_px(lat, lon, world)
    left, top = cx - FRAME / 2 + ox, cy - FRAME / 2 + oy
    n_lat, w_lon = px_to_latlon(left, top, world)
    s_lat, e_lon = px_to_latlon(left + WIN_W, top + WIN_H, world)
    q = f'[out:json][timeout:60];node["place"~"^(city|town)$"]["name"]({s_lat},{w_lon},{n_lat},{e_lon});out;'
    raw = None
    for attempt in range(5):                                   # the public Overpass servers are busy at times
        r = subprocess.run(["curl", "-sS", "-m", "90", "-A", "weather-display-basemap/1.0", "--data-urlencode",
                            "data=" + q, "https://overpass-api.de/api/interpreter"], capture_output=True)
        if r.returncode == 0 and r.stdout.startswith(b"{"):
            raw = r.stdout
            break
        time.sleep(5 * (attempt + 1))
    if raw is None:
        raise SystemExit("Overpass API did not answer - try again later, or use --no-towns")
    out = []
    for e in json.loads(raw)["elements"]:
        t = e.get("tags", {})
        px, py = latlon_to_px(e["lat"], e["lon"], world)
        pop = int(t["population"]) if t.get("population", "").isdigit() else 0
        rank = (t.get("place") == "city", pop)
        out.append((t["name"], rank, round(px - left), round(py - top)))
    return out


def has_text(img, box, pad=14, need=20):
    """True if the map already has dark label text near box (Esri names the bigger places itself)."""
    x0, y0, x1, y1 = (max(0, int(box[0] - pad)), max(0, int(box[1] - pad)),
                      min(WIN_W, int(box[2] + pad)), min(WIN_H, int(box[3] + pad)))
    px = img.crop((x0, y0, x1, y1)).convert("RGB").load()
    dark = sum(1 for yy in range(y1 - y0) for xx in range(x1 - x0) if max(px[xx, yy]) < 120)
    return dark >= need


def draw_towns(win, items, font, limit, avoid=()):
    d = ImageDraw.Draw(win)
    base = win.copy()
    placed = list(avoid)                                   # boxes to keep clear, e.g. the centre marker
    for name, _, x, y in sorted(items, key=lambda i: i[1], reverse=True)[: limit * 3]:
        if len(placed) >= limit:
            break
        w = d.textlength(name, font=font)
        h = font.size
        for bx in (x + 6, x - 6 - w):                      # label right of the dot, or left if no room
            box = (bx - 2, y - h / 2 - 2, bx + w + 2, y + h / 2 + 2)
            if box[0] < 2 or box[2] > WIN_W - 2 or box[1] < 2 or box[3] > WIN_H - 2:
                continue
            if any(not (box[2] < p[0] or box[0] > p[2] or box[3] < p[1] or box[1] > p[3]) for p in placed):
                continue
            if has_text(base, box):
                break
            placed.append(box)
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255), outline=(0, 0, 0))
            d.text((bx, y), name, font=font, fill=(0, 0, 0), anchor="lm", stroke_width=2, stroke_fill=(255, 255, 255))
            break


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lat", type=float)
    ap.add_argument("lon", type=float)
    ap.add_argument("--out", default=".", help="folder to write radar_base_z<N>.png into")
    ap.add_argument("--font", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "calibri.ttf"))
    ap.add_argument("--no-towns", action="store_true", help="skip the town names (no Overpass request)")
    ap.add_argument("--zooms", type=int, nargs="+", default=[5, 6, 7], help="Rainviewer zoom levels")
    a = ap.parse_args()
    ox, oy = (FRAME - WIN_W) // 2, (FRAME - WIN_H) // 2
    cx, cy = FRAME // 2 - ox, FRAME // 2 - oy
    for z in a.zooms:
        full = render(a.lat, a.lon, z + 1, FRAME)
        win = full.crop((ox, oy, ox + WIN_W, oy + WIN_H))
        if not a.no_towns:
            draw_towns(win, towns(a.lat, a.lon, z + 1, ox, oy), ImageFont.truetype(a.font, 15), LABELS_MAX.get(z, 16),
                        avoid=[(cx - 9, cy - 9, cx + 9, cy + 9)])
        d = ImageDraw.Draw(win)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(255, 255, 255), outline=(0, 0, 0), width=1)
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(0, 0, 0))
        path = os.path.join(a.out, f"radar_base_z{z}.png")
        win.save(path, optimize=True)
        print(path, win.size, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
