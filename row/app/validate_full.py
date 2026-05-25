import gc
import json
import sys
import time

import lgfx

from sd_host import TFT_SPI_HOST, SD_SPI_HOST, SD_SLOT, mount_sd


GAME_ROOT = "/sd/game"


def _ensure_game_path():
    if GAME_ROOT in sys.path:
        sys.path.remove(GAME_ROOT)
    sys.path.insert(0, GAME_ROOT)


def _load_asset_base():
    if not mount_sd("/sd", return_ok=True):
        raise RuntimeError("SD_MOUNT_FAILED")
    _ensure_game_path()
    import map_registry

    return map_registry.MAP_REGISTRY[map_registry.MAP1_ID]["asset_base"]


def _load_meta(asset_base):
    with open(asset_base + "/map.json", "r") as f:
        return json.loads(f.read())


def _clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _sprite_fps(frames=180):
    lgfx.sprite_create(240, 320, True)
    colors = (0xF800, 0x07E0, 0x001F, 0xFFFF, 0x0000)
    t0 = time.ticks_ms()
    for i in range(frames):
        lgfx.sprite_fill(colors[i % len(colors)])
        lgfx.sprite_push(0, 0)
    dt = time.ticks_diff(time.ticks_ms(), t0)
    return (frames * 1000 / dt) if dt else 0.0


def _tile_dirty_fps(meta, asset_base, frames=300):
    tile = meta["tile_size"]
    map_w = meta["map_w"]
    map_h = meta["map_h"]
    view_w = 240
    view_h = 320
    world_w = map_w * tile
    world_h = map_h * tile
    tile_count = meta.get("tileset_count", 0)
    spawn_x = meta.get("spawn_x", world_w // 2)
    spawn_y = meta.get("spawn_y", world_h // 2)

    if not lgfx.tile_setup(tile, map_w, map_h, view_w, view_h, True):
        raise RuntimeError("tile_setup failed")
    if not lgfx.tile_load_files(asset_base + "/tileset.bin", asset_base + "/tilemap.bin"):
        raise RuntimeError("tile_load failed")

    x = spawn_x
    y = spawn_y
    vx = 3
    vy = 2
    t0 = time.ticks_ms()
    for i in range(frames):
        x += vx
        y += vy
        if x < 0 or x > world_w - 1:
            vx = -vx
        if y < 0 or y > world_h - 1:
            vy = -vy
        x = _clamp(x, 0, world_w - 1)
        y = _clamp(y, 0, world_h - 1)

        sx = _clamp(x - view_w // 2, 0, world_w - view_w)
        sy = _clamp(y - view_h // 2, 0, world_h - view_h)
        lgfx.tile_render(sx, sy, False)
        lgfx.draw_player(x - sx, y - sy, 0xF800, 4)

        if tile_count > 1 and (i % 30) == 0:
            tx = x // tile
            ty = y // tile
            lgfx.tile_set(tx, ty, (i // 30) % tile_count)

        if (i % 120) == 0:
            gc.collect()

    dt = time.ticks_diff(time.ticks_ms(), t0)
    return ((frames * 1000 / dt) if dt else 0.0), lgfx.stats()


def _stability_seconds(seconds=120):
    lgfx.sprite_create(240, 320, True)
    colors = (0x0000, 0xF800, 0x07E0, 0x001F, 0xFFFF)
    frames = 0
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < seconds * 1000:
        lgfx.sprite_fill(colors[frames % len(colors)])
        lgfx.sprite_push(0, 0)
        frames += 1
        if (frames % 300) == 0:
            gc.collect()
    dt = time.ticks_diff(time.ticks_ms(), t0)
    return frames, dt, lgfx.stats(), gc.mem_free()


print("SPI fixed:", "TFT=SPI%d" % TFT_SPI_HOST, "SD=SPI%d" % SD_SPI_HOST, "SD slot=%d" % SD_SLOT)
asset_base = _load_asset_base()
meta = _load_meta(asset_base)

lgfx.init()
gc.collect()
mem_before = gc.mem_free()

sprite_fps = _sprite_fps(180)
tile_fps, tile_stats = _tile_dirty_fps(meta, asset_base, 300)
stable_frames, stable_dt, stable_stats, mem_after = _stability_seconds(120)

print("asset:", asset_base)
print("sprite_fps:", sprite_fps)
print("tile_fps:", tile_fps, "tile_stats:", tile_stats)
print("stability_frames:", stable_frames, "elapsed_ms:", stable_dt)
print("stability_fps:", (stable_frames * 1000 / stable_dt) if stable_dt else 0)
print("mem_free_before:", mem_before, "mem_free_after:", mem_after, "delta:", mem_after - mem_before)
print("final_stats:", stable_stats)
print("validate_full done")
