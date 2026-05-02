import json
import os
import time
import lgfx


ASSET_BASE = "/sd/out"


def _must_load_meta(base):
    with open(base + "/map.json", "r") as f:
        return json.loads(f.read())


def _print_asset_file_info(base):
    names = ("map.json", "tilemap.bin", "tileset.bin")
    for name in names:
        path = base + "/" + name
        try:
            st = os.stat(path)
            print("asset_file:", path, "size:", st[6])
        except OSError:
            print("asset_file:", path, "missing")


def _clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


print("asset_base:", ASSET_BASE)
_print_asset_file_info(ASSET_BASE)
meta = _must_load_meta(ASSET_BASE)

tile = meta["tile_size"]
map_w = meta["map_w"]
map_h = meta["map_h"]
world_w = map_w * tile
world_h = map_h * tile

lgfx.init()
ok = lgfx.tile_setup(tile, map_w, map_h, 240, 320, True)
print("tile_setup:", ok)
if hasattr(lgfx, "tile_loader_mode"):
    print("tile_loader_mode:", lgfx.tile_loader_mode())

ok = lgfx.tile_load_files(ASSET_BASE + "/tileset.bin", ASSET_BASE + "/tilemap.bin")
print("tile_load:", ok)
if not ok and hasattr(lgfx, "tile_last_error"):
    print("tile_last_error:", lgfx.tile_last_error())
    raise RuntimeError("tile_load failed")

scroll_x = 0
scroll_y = 0
dx = 3
dy = 2

t0 = time.ticks_ms()
for _ in range(120):
    scroll_x += dx
    scroll_y += dy
    max_x = world_w - 240
    max_y = world_h - 320
    if scroll_x <= 0 or scroll_x >= max_x:
        dx = -dx
    if scroll_y <= 0 or scroll_y >= max_y:
        dy = -dy
    scroll_x = _clamp(scroll_x, 0, max_x)
    scroll_y = _clamp(scroll_y, 0, max_y)
    lgfx.tile_render(scroll_x, scroll_y, False)

dt = time.ticks_diff(time.ticks_ms(), t0)
print("tile fps:", (120000 / dt) if dt else 0)
print("stats:", lgfx.stats())
