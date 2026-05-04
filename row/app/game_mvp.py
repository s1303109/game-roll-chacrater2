import gc
import json
import os
import time
from machine import ADC, Pin
import lgfx


SD_READY = False
DISPLAY_INIT_DONE = False


def _try_mount_sd():
    global SD_READY
    try:
        from sd_host import mount_sd
    except Exception:
        SD_READY = False
        return
    SD_READY = False
    for freq in (8_000_000, 4_000_000, 12_000_000, 20_000_000):
        try:
            SD_READY = bool(mount_sd("/sd", freq=freq, return_ok=True))
        except Exception:
            SD_READY = False
        if SD_READY:
            print("sd_freq:", freq)
            break
    print("sd_mounted:", SD_READY)


def _find_asset_base(base_list):
    for base in base_list:
        if base.startswith("/sd/") and not SD_READY:
            continue
        try:
            with open(base + "/map.json", "r") as f:
                text = f.read()
        except OSError:
            continue
        try:
            meta = json.loads(text)
        except ValueError:
            raise ValueError("MAP_JSON_INVALID")
        _validate_meta(meta)
        return base, meta
    raise RuntimeError("ASSET_MISSING")


def _clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _validate_meta(meta):
    for key in ("tile_size", "map_w", "map_h"):
        if key not in meta:
            raise ValueError("MAP_JSON_INVALID")


def _file_size(path):
    try:
        return os.stat(path)[6]
    except OSError:
        return -1


def _path_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _sync_sd_assets_from_remote_if_needed():
    if not ENABLE_AUTO_SD_SYNC:
        return
    if not SD_READY:
        return
    if not _path_exists(REMOTE_ASSET_BASE + "/map.json"):
        return

    names = ("map.json", "tilemap.bin", "tileset.bin", "collision.bin", PLAYER_SHEET_NAME)
    needs_sync = False
    for name in names:
        src_size = _file_size(REMOTE_ASSET_BASE + "/" + name)
        if src_size < 0:
            return
        dst_size = _file_size(SD_ASSET_BASE + "/" + name)
        if dst_size != src_size:
            needs_sync = True
            break

    if not needs_sync:
        return

    try:
        import copy_assets_to_sd
        print("sd_sync: updated_from_remote")
        del copy_assets_to_sd
    except Exception as err:
        print("sd_sync_failed:", err)


def _print_asset_files(base, meta):
    names = ["map.json", "tilemap.bin", "tileset.bin", PLAYER_SHEET_NAME]
    collision_name = meta.get("collision")
    if collision_name:
        names.append(collision_name)
    for name in names:
        path = base + "/" + name
        size = _file_size(path)
        if size >= 0:
            print("asset_file:", path, "size:", size)
        else:
            print("asset_file:", path, "missing")


def _load_collision(meta, base, map_w, map_h):
    expected = map_w * map_h
    last_err = None

    # Prefer collision in the selected base first, then probe fallback bases.
    bases = [base]
    for b in ASSET_BASES:
        if b != base:
            bases.append(b)

    for src_base in bases:
        src_meta = meta
        if src_base != base:
            try:
                with open(src_base + "/map.json", "r") as f:
                    src_meta = json.loads(f.read())
            except OSError:
                continue
            except ValueError:
                continue
            if (
                src_meta.get("tile_size") != meta.get("tile_size")
                or src_meta.get("map_w") != map_w
                or src_meta.get("map_h") != map_h
            ):
                continue

        name = src_meta.get("collision")
        if not name:
            continue
        if src_meta.get("collision_format", "u8") != "u8":
            last_err = "COLLISION_FORMAT_UNSUPPORTED"
            continue
        try:
            with open(src_base + "/" + name, "rb") as f:
                data = f.read()
        except OSError:
            last_err = "COLLISION_MISSING"
            continue
        if len(data) != expected:
            last_err = "COLLISION_SIZE_MISMATCH expected=%d got=%d" % (expected, len(data))
            continue
        if src_base != base:
            print("collision_fallback:", src_base + "/" + name)
        return data, None

    if last_err:
        return None, last_err
    return None, "COLLISION_NOT_DECLARED"


def _read_file(path):
    with open(path, "rb") as f:
        return f.read()


def _swap16(buf):
    if not buf:
        return buf
    data = bytearray(buf)
    for i in range(0, len(data), 2):
        data[i], data[i + 1] = data[i + 1], data[i]
    return bytes(data)


def _validate_tile_files(base, tile, map_w, map_h):
    tilemap_path = base + "/tilemap.bin"
    tileset_path = base + "/tileset.bin"
    tilemap_size = _file_size(tilemap_path)
    tileset_size = _file_size(tileset_path)
    expected_tilemap = map_w * map_h * 2
    tile_bytes = tile * tile * 2

    if tilemap_size < 0:
        return "TILEMAP_MISSING"
    if tilemap_size != expected_tilemap:
        return "TILEMAP_SIZE_MISMATCH expected=%d got=%d" % (expected_tilemap, tilemap_size)
    if tileset_size < 0:
        return "TILESET_MISSING"
    if tile_bytes <= 0 or (tileset_size % tile_bytes) != 0:
        return "TILESET_SIZE_INVALID expected_multiple=%d got=%d" % (tile_bytes, tileset_size)
    return None


def _load_tiles(meta, base, tile, map_w, map_h):
    meta_endian = meta.get("endian", "little")
    if meta_endian not in ("little", "big"):
        raise RuntimeError("TILE_ENDIAN_UNSUPPORTED")

    err = _validate_tile_files(base, tile, map_w, map_h)
    if err:
        raise RuntimeError(err)

    tilemap_path = base + "/tilemap.bin"
    tileset_path = base + "/tileset.bin"
    stream_ok = meta_endian == "little" and hasattr(lgfx, "tile_load_files")

    # Prefer eager in-memory load for stable scrolling (avoids SD stream misses).
    gc.collect()
    try:
        tileset = _read_file(tileset_path)
        tilemap = _read_file(tilemap_path)
        if meta_endian == "big":
            tileset = _swap16(tileset)
            tilemap = _swap16(tilemap)
        if lgfx.tile_load(tileset, tilemap):
            print("tile_loader: memory")
            return "little"
        print("tile_loader_memory_fail")
    except MemoryError:
        print("tile_loader_memory_oom mem_free:", gc.mem_free())

    # On little-endian assets, fall back to file streaming if RAM load is not possible.
    if stream_ok:
        if lgfx.tile_load_files(tileset_path, tilemap_path):
            print("tile_loader: stream")
            return "little"

        code = "TILE_LOAD_FAIL"
        if hasattr(lgfx, "tile_last_error"):
            err = lgfx.tile_last_error()
            if err == 2:
                code = "TILEMAP_MISSING"
            elif err == 3:
                code = "TILEMAP_INVALID"
            elif err == 4:
                code = "TILESET_MISSING"
            elif err == 5:
                code = "TILESET_SEEK_FAIL"
            elif err == 6:
                code = "TILESET_SIZE_INVALID"
            elif err == 7:
                code = "TILESET_FORMAT_INVALID"
            elif err == 8:
                code = "TILE_CACHE_ALLOC_FAIL"
        raise RuntimeError(code)

    # Big-endian assets must be memory-loaded for byte-swap.
    raise RuntimeError("TILE_OOM")


def _isqrt(n):
    if n <= 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def _infer_player_sheet_dims(buf_len):
    if buf_len <= 0 or (buf_len % 2) != 0:
        return None, "PLAYER_SHEET_LEN_INVALID"
    pixels = buf_len // 2
    side = _isqrt(pixels)
    if side * side != pixels:
        return None, "PLAYER_SHEET_NOT_SQUARE"
    if side % 3 != 0:
        return None, "PLAYER_SHEET_NOT_3X3"
    frame = side // 3
    if frame <= 0:
        return None, "PLAYER_SHEET_FRAME_INVALID"
    return (side, side, frame, frame), None


def _load_player_sheet(base):
    global PLAYER_FRAME_W, PLAYER_FRAME_H
    if not hasattr(lgfx, "player_sheet_load") or not hasattr(lgfx, "player_frame_set") or not hasattr(lgfx, "player_sheet_clear"):
        print("player_sheet_api_missing: fallback_red_dot")
        return False, "PLAYER_SHEET_API_MISSING"

    lgfx.player_sheet_clear()
    last_err = "PLAYER_SHEET_MISSING"
    paths = []

    def _add_path(path):
        if path not in paths:
            paths.append(path)

    _add_path(base + "/" + PLAYER_SHEET_NAME)
    for b in ASSET_BASES:
        _add_path(b + "/" + PLAYER_SHEET_NAME)
    for p in PLAYER_SHEET_FALLBACK_PATHS:
        _add_path(p)

    for path in paths:
        file_len = _file_size(path)
        if file_len < 0:
            last_err = "PLAYER_SHEET_FILE_MISSING " + path
            continue

        dims, dim_err = _infer_player_sheet_dims(file_len)
        if dim_err:
            last_err = dim_err + " len=%d path=%s" % (file_len, path)
            print("player_sheet_invalid:", last_err)
            continue

        sheet_w, sheet_h, frame_w, frame_h = dims
        PLAYER_FRAME_W = frame_w
        PLAYER_FRAME_H = frame_h
        if hasattr(lgfx, "player_sheet_load_file") and lgfx.player_sheet_load_file(path, sheet_w, sheet_h, frame_w, frame_h):
            print("player_sheet_loaded:", path, "sheet:", sheet_w, sheet_h, "frame:", frame_w, frame_h)
            return True, None

        try:
            gc.collect()
            buf = _read_file(path)
        except MemoryError:
            last_err = "PLAYER_SHEET_OOM " + path
            print("player_sheet_oom:", path, "mem_free:", gc.mem_free())
            continue

        if lgfx.player_sheet_load(buf, sheet_w, sheet_h, frame_w, frame_h):
            print("player_sheet_loaded_fallback:", path, "sheet:", sheet_w, sheet_h, "frame:", frame_w, frame_h)
            return True, None

        last_err = "PLAYER_SHEET_LOAD_FAIL path=%s" % path
        print("player_sheet_load_fail:", path, "len:", file_len, "sheet:", sheet_w, sheet_h, "frame:", frame_w, frame_h)

    lgfx.player_sheet_clear()
    print("player_sheet_fallback_red_dot:", last_err)
    return False, last_err


SD_ASSET_BASE = "/sd/out"
REMOTE_ASSET_BASE = "/remote/assets/out"
ASSET_BASES = ("/", SD_ASSET_BASE, REMOTE_ASSET_BASE)
ENABLE_AUTO_SD_SYNC = False
ENABLE_SD_MOUNT = False
PLAYER_SHEET_NAME = "player_sheet.rgb565"
PLAYER_SHEET_FALLBACK_PATHS = (
    "/player_sheet.rgb565",
)
ENABLE_SPAWN_OVERLAY = False
SPAWN_OVERLAY_PATH = "/main character close eyes.png"
FORCE_SIMPLE_PLAYER = False
USE_TILE_RENDER_PLAYER_COMPOSE = True
ROTATION = 1
VIEW_W = 320
VIEW_H = 240
ACTIVE_VIEW_W = VIEW_W
ACTIVE_VIEW_H = VIEW_H
PLAYER_R = 4
PLAYER_FRAME_W = 29
PLAYER_FRAME_H = 29
PLAYER_COLOR = 0xF800
JOY_X_PIN = 1
JOY_Y_PIN = 2
ENCOUNTER_SW_PIN = 15
BTN_FIGHT_PIN = 38
BTN_ACT_PIN = 39
BTN_ITEM_PIN = 40
BTN_MERCY_PIN = 41
TARGET_FRAME_MS = 16
DEADZONE_DIV = 7
ENTER_DIV = 4
EXIT_DIV = 6
ADC_SAMPLES = 4
MOVE_STEP = 2
MOVE_DT_MAX_SCALE = 4
MOVE_MAX_PIXELS_PER_FRAME = 4
SCROLL_STEP = 1
SCROLL_FOLLOW_MIN_PER_FRAME = 1
SCROLL_FOLLOW_MAX_PER_FRAME = 3
SCROLL_FOLLOW_FAST_GAP = 6
SCROLL_FOLLOW_ACTIVE_BONUS_GAP = 3
SCROLL_FOLLOW_ACTIVE_BONUS = 1
SCROLL_FOLLOW_DT_MAX_SCALE = 1
SCROLL_SETTLE_BONUS = 1
CAM_HARD_LOCK_PAD = 24
CAM_CENTER_DEADBAND_X = 0
CAM_CENTER_DEADBAND_Y = 0
FORCE_FULL_REDRAW_WHEN_SCROLLED = False
INSTANT_CAMERA_FOLLOW = True
FULL_VIEW_SETUP_RETRIES = 20
ALLOW_VIEW_FALLBACK = True
PLAYER_ANIM_STEP_MS = 120
ANIM_IDLE_HOLD_MS = 90
PLAYER_ANIM_ROW_FRONT = 0
PLAYER_ANIM_ROW_SIDE = 1
MODE_EXPLORE = 0
MODE_BATTLE_MENU = 1
MODE_BATTLE_FIGHT = 2
ENCOUNTER_COOLDOWN_FRAMES = 120
BATTLE_FRAME_W = 240
BATTLE_FRAME_H = 200
BATTLE_BORDER_THICK = 2
BATTLE_FRAME_BORDER_THICK = 4
BATTLE_CMD_MARGIN_X = 8
BATTLE_CMD_GAP = 4
BATTLE_CMD_H = 24
BATTLE_CMD_BORDER_THICK = 2
BATTLE_COLOR_WHITE = 0xFFFF
BATTLE_COLOR_RED = 0xF800
BATTLE_HEART_R = 5
BATTLE_HEART_SPRITE_PATH = "/heart_clean_18.png"
BATTLE_HEART_SPRITE_FALLBACK_PATH = "/heart.png"
BATTLE_HEART_SPRITE_W = 18
BATTLE_HEART_SPRITE_H = 18
BATTLE_HEART_HIT_R = 9
BATTLE_HEART_ERASE_R = BATTLE_HEART_HIT_R + 1
BATTLE_HEART_FAST_R = 7
BATTLE_HEART_STEP = 2
BATTLE_HEART_USE_PNG_ON_MOVE = True
ENEMY_SPRITE_PATH = "/enemy.png"
ENEMY_SPRITE_W = 72
ENEMY_SPRITE_H = 72
ACT_DIALOG_TEXT_PATH = "/act_dialog_text.png"
MERCY_DIALOG_TEXT_PATH = "/mercy_dialog_text.png"
LAMP_DIALOG_TEXT_PATH = "/lamp_dialog_text.png"
LEAF_BATTLE_RECT_PX = (128, 304, 96, 64)
# Expand to cover the full triple-lamp poles and nearby interaction area.
LAMP_INTERACT_RECT_PX = (160, 624, 128, 192)
MAP1_ID = 1
MAP2_ID = 2
MAP2_LOCAL_ASSET_BASE = "/out_map2"
MAP2_ASSET_BASE = "/sd/out_map2"
MAP2_REMOTE_ASSET_BASE = "/remote/assets/out_map2"
MAP2_ASSET_BASES = (MAP2_LOCAL_ASSET_BASE, MAP2_ASSET_BASE, MAP2_REMOTE_ASSET_BASE)
MAP1_PORTAL_TO_MAP2_RECT_PX = (304, 160, 32, 96)
MAP2_PORTAL_TO_MAP1_RECT_PX = (760, 120, 80, 120)
TELEPORT_COOLDOWN_FRAMES = 30
LAMP_DIALOG_TEXT_W = 214
LAMP_DIALOG_TEXT_H = 27
ACT_DIALOG_MS = 1000
MERCY_DIALOG_MS = 2500
LAMP_DIALOG_MS = 2000
PLAYER_HP_MAX = 20
MONSTER_NAME = "Grim Reaper"
BULLET_R = 3
BULLET_SPEED_PX = 2
BULLET_SPAWN_INTERVAL_MS = 300
DAMAGE_INVULN_MS = 450
BULLET_FP_SHIFT = 8
BATTLE_STATUS_TO_CMD_GAP = 2
FIGHT_AUTO_RETURN_MS = 7000
BUILD_TAG = "game_mvp_tune29_heart_sprite_io_tune_20260502"

print("build:", BUILD_TAG)

if ENABLE_SD_MOUNT:
    _try_mount_sd()
    _sync_sd_assets_from_remote_if_needed()
else:
    SD_READY = False
    print("sd_mounted:", SD_READY, "(disabled)")
asset_base, meta = _find_asset_base(ASSET_BASES)
print("asset:", asset_base)
if asset_base == SD_ASSET_BASE:
    _print_asset_files(asset_base, meta)
tile = meta["tile_size"]
map_w = meta["map_w"]
map_h = meta["map_h"]
world_w = map_w * tile
world_h = map_h * tile

spawn_x = meta.get("spawn_x", world_w // 2)
spawn_y = meta.get("spawn_y", world_h // 2)
player_x = spawn_x
player_y = spawn_y

if not DISPLAY_INIT_DONE:
    lgfx.init()
    DISPLAY_INIT_DONE = True
lgfx.set_rotation(ROTATION)
meta_endian = meta.get("endian", "little")
if hasattr(lgfx, "set_swap_bytes"):
    lgfx.set_swap_bytes(meta_endian == "little")


def _tile_setup_with_fallback():
    global ACTIVE_VIEW_W, ACTIVE_VIEW_H

    # Fast path: try target fullscreen directly first.
    gc.collect()
    if lgfx.tile_setup(tile, map_w, map_h, VIEW_W, VIEW_H, False):
        ACTIVE_VIEW_W, ACTIVE_VIEW_H = VIEW_W, VIEW_H
        print("tile_setup:", VIEW_W, VIEW_H, "psram:", False)
        return
    gc.collect()
    if lgfx.tile_setup(tile, map_w, map_h, VIEW_W, VIEW_H, True):
        ACTIVE_VIEW_W, ACTIVE_VIEW_H = VIEW_W, VIEW_H
        print("tile_setup:", VIEW_W, VIEW_H, "psram:", True)
        return

    def _try_setup(vw, vh, use_psram_order, retries):
        global ACTIVE_VIEW_W, ACTIVE_VIEW_H
        for _ in range(retries):
            for use_psram in use_psram_order:
                gc.collect()
                if lgfx.tile_setup(tile, map_w, map_h, vw, vh, use_psram):
                    ACTIVE_VIEW_W, ACTIVE_VIEW_H = vw, vh
                    print("tile_setup:", vw, vh, "psram:", use_psram)
                    return True
        return False

    # Fullscreen is the intended mode. Retry it first, preferring internal RAM
    # to avoid unstable SPIRAM-path allocation failures on boards without PSRAM.
    if VIEW_W <= world_w and VIEW_H <= world_h:
        if _try_setup(VIEW_W, VIEW_H, (False, True), FULL_VIEW_SETUP_RETRIES):
            return
        if not ALLOW_VIEW_FALLBACK:
            raise RuntimeError("TILE_SETUP_FULLSCREEN_FAIL")

    # Fall back to progressively smaller views when memory is tight.
    candidates = (
        # Prefer full display width first, so perceived map scale stays close.
        (320, 224),
        (320, 208),
        (320, 192),
        (304, 224),
        (288, 216),
        (272, 204),
        (256, 192),
        (240, 180),
        (224, 168),
        (208, 156),
        (200, 150),
        (192, 144),
        (176, 132),
        (160, 120),
    )

    for vw, vh in candidates:
        if vw > world_w or vh > world_h:
            continue
        if _try_setup(vw, vh, (False, True), 1):
            return
    raise RuntimeError("TILE_SETUP_FAIL")


def _render_scene(scroll_x, scroll_y, player_x, player_y, force_full):
    if USE_TILE_RENDER_PLAYER_COMPOSE and hasattr(lgfx, "tile_render_player"):
        lgfx.tile_render_player(scroll_x, scroll_y, player_x - scroll_x, player_y - scroll_y, PLAYER_COLOR, PLAYER_R, force_full)
    else:
        lgfx.tile_render(scroll_x, scroll_y, force_full)
        lgfx.draw_player(player_x - scroll_x, player_y - scroll_y, PLAYER_COLOR, PLAYER_R)

if hasattr(lgfx, "player_sheet_clear"):
    # Release previous C-side sheet buffers before sprite allocation fallback.
    lgfx.player_sheet_clear()
gc.collect()

if hasattr(lgfx, "player_sheet_load_file"):
    _tile_setup_with_fallback()
    player_sheet_enabled, player_sheet_err = _load_player_sheet(asset_base)
else:
    player_sheet_enabled, player_sheet_err = _load_player_sheet(asset_base)
    _tile_setup_with_fallback()

if FORCE_SIMPLE_PLAYER:
    player_sheet_enabled = False
    if hasattr(lgfx, "player_sheet_clear"):
        lgfx.player_sheet_clear()

if not player_sheet_enabled and player_sheet_err:
    print("player_mode: red_dot", player_sheet_err)

print("view:", ACTIVE_VIEW_W, ACTIVE_VIEW_H)


def _update_battle_layout():
    inner_inset = BATTLE_FRAME_BORDER_THICK
    if BATTLE_BORDER_THICK > inner_inset:
        inner_inset = BATTLE_BORDER_THICK
    frame_x = (ACTIVE_VIEW_W - BATTLE_FRAME_W) // 2
    frame_y = (ACTIVE_VIEW_H - BATTLE_FRAME_H) // 2
    if frame_x < 0:
        frame_x = 0
    if frame_y < 0:
        frame_y = 0
    frame_x_max = frame_x + BATTLE_FRAME_W
    frame_y_max = frame_y + BATTLE_FRAME_H
    heart_init_x = frame_x + (BATTLE_FRAME_W // 2)
    heart_init_y = frame_y + (BATTLE_FRAME_H // 2)
    # Keep enough inset so erase radius never touches thick frame border.
    heart_min_x = frame_x + inner_inset + BATTLE_HEART_ERASE_R
    heart_max_x = frame_x + BATTLE_FRAME_W - inner_inset - BATTLE_HEART_ERASE_R - 1
    heart_min_y = frame_y + inner_inset + BATTLE_HEART_ERASE_R
    heart_max_y = frame_y + BATTLE_FRAME_H - inner_inset - BATTLE_HEART_ERASE_R - 1
    cmd_y = frame_y + BATTLE_FRAME_H - BATTLE_CMD_H - 10
    cmd_w = (BATTLE_FRAME_W - (BATTLE_CMD_MARGIN_X * 2) - (BATTLE_CMD_GAP * 3)) // 4
    cmd_x0 = frame_x + BATTLE_CMD_MARGIN_X
    return (
        frame_x,
        frame_y,
        frame_x_max,
        frame_y_max,
        heart_init_x,
        heart_init_y,
        heart_min_x,
        heart_max_x,
        heart_min_y,
        heart_max_y,
        cmd_x0,
        cmd_y,
        cmd_w,
    )


(
    battle_frame_x,
    battle_frame_y,
    battle_frame_x_max,
    battle_frame_y_max,
    battle_heart_init_x,
    battle_heart_init_y,
    battle_heart_min_x,
    battle_heart_max_x,
    battle_heart_min_y,
    battle_heart_max_y,
    battle_cmd_x0,
    battle_cmd_y,
    battle_cmd_w,
) = _update_battle_layout()

runtime_endian = _load_tiles(meta, asset_base, tile, map_w, map_h)
if hasattr(lgfx, "set_swap_bytes"):
    lgfx.set_swap_bytes(runtime_endian == "little")
collision, collision_err = _load_collision(meta, asset_base, map_w, map_h)
if collision_err:
    print("collision_error:", collision_err)
if collision is None:
    raise RuntimeError("COLLISION_REQUIRED")
blocked_tiles = 0
for v in collision:
    if v:
        blocked_tiles += 1
print("collision_tiles:", blocked_tiles, "/", map_w * map_h)
if blocked_tiles == 0:
    raise RuntimeError("COLLISION_EMPTY")


def _collides(nx, ny, r):
    if collision is None:
        return False
    left = (nx - r) // tile
    right = (nx + r) // tile
    top = (ny - r) // tile
    bottom = (ny + r) // tile
    for ty in range(top, bottom + 1):
        row_base = ty * map_w
        for tx in range(left, right + 1):
            if tx < 0 or ty < 0 or tx >= map_w or ty >= map_h:
                return True
            if collision[row_base + tx]:
                return True
    return False


def _collision_selftest():
    # Sanity check: at least one blocked tile center must collide.
    for i in range(map_w * map_h):
        if collision[i]:
            tx = i % map_w
            ty = i // map_w
            cx = tx * tile + (tile // 2)
            cy = ty * tile + (tile // 2)
            if not _collides(cx, cy, 0):
                raise RuntimeError("COLLISION_SELFTEST_FAIL")
            return
    raise RuntimeError("COLLISION_EMPTY")


_collision_selftest()


def _load_map_context(base, fallback_all_walkable=False):
    global asset_base, meta, tile, map_w, map_h, world_w, world_h, runtime_endian, collision

    with open(base + "/map.json", "r") as f:
        new_meta = json.loads(f.read())
    _validate_meta(new_meta)

    asset_base = base
    meta = new_meta
    tile = meta["tile_size"]
    map_w = meta["map_w"]
    map_h = meta["map_h"]
    world_w = map_w * tile
    world_h = map_h * tile

    _tile_setup_with_fallback()
    runtime_endian = _load_tiles(meta, asset_base, tile, map_w, map_h)
    if hasattr(lgfx, "set_swap_bytes"):
        lgfx.set_swap_bytes(runtime_endian == "little")

    collision_data, collision_err = _load_collision(meta, asset_base, map_w, map_h)
    if fallback_all_walkable or collision_data is None:
        collision = bytearray(map_w * map_h)
        if collision_err:
            print("collision_fallback_all_walkable:", collision_err)
        blocked_tiles = 0
    else:
        collision = collision_data
        blocked_tiles = 0
        for v in collision:
            if v:
                blocked_tiles += 1
        if blocked_tiles == 0:
            raise RuntimeError("COLLISION_EMPTY")
        _collision_selftest()
    print("collision_tiles:", blocked_tiles, "/", map_w * map_h)


def switch_map(target_map_id, spawn_x=None, spawn_y=None):
    global collision, meta, asset_base, current_map_id
    global player_x, player_y, scroll_x, scroll_y
    global prev_scroll_x, prev_scroll_y, prev_player_x, prev_player_y
    global leaf_zone_prev_inside, explore_overlay_dirty, lamp_dialog_until_ms
    global explore_force_full_redraw, teleport_cooldown_frames
    global tile, map_w, map_h, world_w, world_h, runtime_endian

    fallback_all_walkable = False
    if target_map_id == MAP2_ID:
        try:
            next_base, _ = _find_asset_base(MAP2_ASSET_BASES)
            fallback_all_walkable = True
        except Exception as err:
            print("switch_map_skip_map2:", err)
            teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
            return False
    else:
        next_base, _ = _find_asset_base(ASSET_BASES)

    prev_collision = collision
    prev_meta = meta
    prev_asset_base = asset_base
    prev_tile = tile
    prev_map_w = map_w
    prev_map_h = map_h
    prev_world_w = world_w
    prev_world_h = world_h
    prev_runtime_endian = runtime_endian
    prev_player_x_saved = player_x
    prev_player_y_saved = player_y
    prev_scroll_x_saved = scroll_x
    prev_scroll_y_saved = scroll_y
    prev_prev_scroll_x_saved = prev_scroll_x
    prev_prev_scroll_y_saved = prev_scroll_y
    prev_prev_player_x_saved = prev_player_x
    prev_prev_player_y_saved = prev_player_y
    prev_current_map_id = current_map_id

    collision = None
    meta = None
    asset_base = None
    gc.collect()

    try:
        _load_map_context(next_base, fallback_all_walkable=fallback_all_walkable)
    except Exception as err:
        collision = prev_collision
        meta = prev_meta
        asset_base = prev_asset_base
        tile = prev_tile
        map_w = prev_map_w
        map_h = prev_map_h
        world_w = prev_world_w
        world_h = prev_world_h
        runtime_endian = prev_runtime_endian
        player_x = prev_player_x_saved
        player_y = prev_player_y_saved
        scroll_x = prev_scroll_x_saved
        scroll_y = prev_scroll_y_saved
        prev_scroll_x = prev_prev_scroll_x_saved
        prev_scroll_y = prev_prev_scroll_y_saved
        prev_player_x = prev_prev_player_x_saved
        prev_player_y = prev_prev_player_y_saved
        current_map_id = prev_current_map_id
        print("switch_map_restore:", err)
        teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
        gc.collect()
        return False

    if spawn_x is None:
        spawn_x = meta.get("spawn_x", world_w // 2)
    if spawn_y is None:
        spawn_y = meta.get("spawn_y", world_h // 2)

    player_x = _clamp(spawn_x, PLAYER_R, world_w - PLAYER_R - 1)
    player_y = _clamp(spawn_y, PLAYER_R, world_h - PLAYER_R - 1)
    scroll_x = _clamp(player_x - ACTIVE_VIEW_W // 2, 0, world_w - ACTIVE_VIEW_W)
    scroll_y = _clamp(player_y - ACTIVE_VIEW_H // 2, 0, world_h - ACTIVE_VIEW_H)
    prev_scroll_x = scroll_x
    prev_scroll_y = scroll_y
    prev_player_x = player_x
    prev_player_y = player_y

    leaf_zone_prev_inside = False
    explore_overlay_dirty = False
    lamp_dialog_until_ms = 0
    explore_force_full_redraw = True
    teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
    current_map_id = target_map_id
    gc.collect()
    return True


adc_x = ADC(Pin(JOY_X_PIN))
adc_y = ADC(Pin(JOY_Y_PIN))
adc_x.atten(ADC.ATTN_11DB)
adc_y.atten(ADC.ATTN_11DB)
interact_sw = Pin(ENCOUNTER_SW_PIN, Pin.IN, Pin.PULL_UP)
btn_fight = Pin(BTN_FIGHT_PIN, Pin.IN, Pin.PULL_UP)
btn_act = Pin(BTN_ACT_PIN, Pin.IN, Pin.PULL_UP)
btn_item = Pin(BTN_ITEM_PIN, Pin.IN, Pin.PULL_UP)
btn_mercy = Pin(BTN_MERCY_PIN, Pin.IN, Pin.PULL_UP)


def _adc_read(adc):
    if hasattr(adc, "read_u16"):
        return adc.read_u16(), 65535
    return adc.read(), 4095


def _axis_dir(raw, center, axis_max, prev_dir):
    delta = raw - center
    enter = axis_max // ENTER_DIV
    leave = axis_max // EXIT_DIV
    if prev_dir > 0:
        if delta <= leave:
            return 0
        return 1
    if prev_dir < 0:
        if delta >= -leave:
            return 0
        return -1
    if delta >= enter:
        return 1
    if delta <= -enter:
        return -1
    return 0


def _adc_read_avg(adc, samples):
    total = 0
    axis_max = 4095
    for _ in range(samples):
        v, m = _adc_read(adc)
        total += v
        axis_max = m
    return total // samples, axis_max


def _read_falling_edge(pin, prev_state):
    state = pin.value()
    return state, (prev_state == 1 and state == 0)


def _in_rect(px, py, rect):
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return False
    return x <= px < (x + w) and y <= py < (y + h)


def _scaled_axis_delta(direction, base_step, frame_dt, carry):
    if direction == 0:
        return 0, 0

    base_ms = TARGET_FRAME_MS if TARGET_FRAME_MS > 0 else 20
    dt = frame_dt
    max_dt = base_ms * MOVE_DT_MAX_SCALE
    if dt > max_dt:
        dt = max_dt

    budget = direction * base_step * dt + carry
    if budget >= 0:
        delta = budget // base_ms
    else:
        delta = -((-budget) // base_ms)
    carry = budget - delta * base_ms

    if delta > MOVE_MAX_PIXELS_PER_FRAME:
        delta = MOVE_MAX_PIXELS_PER_FRAME
    elif delta < -MOVE_MAX_PIXELS_PER_FRAME:
        delta = -MOVE_MAX_PIXELS_PER_FRAME

    return delta, carry


def _move_axis_with_collision(pos, other_pos, delta, is_x):
    if delta == 0:
        return pos

    step = 1 if delta > 0 else -1
    if is_x:
        lo = PLAYER_R
        hi = world_w - PLAYER_R - 1
    else:
        lo = PLAYER_R
        hi = world_h - PLAYER_R - 1

    for _ in range(delta if delta > 0 else -delta):
        nxt = pos + step
        if nxt < lo:
            nxt = lo
        elif nxt > hi:
            nxt = hi
        if nxt == pos:
            break

        if is_x:
            if _collides(nxt, other_pos, PLAYER_R):
                break
        else:
            if _collides(other_pos, nxt, PLAYER_R):
                break

        pos = nxt

    return pos


def _camera_chase_axis(scroll, target, move_axis, frame_dt):
    delta = target - scroll
    if delta == 0:
        return scroll

    ad = delta if delta > 0 else -delta

    # Keep micro-scroll updates fine-grained, then ramp up only for larger gaps.
    step = SCROLL_FOLLOW_MIN_PER_FRAME + (ad // SCROLL_FOLLOW_FAST_GAP)

    # While the stick is still pushing toward the same direction, bias one extra step
    # once the gap is visible, preserving responsiveness without hard snapping.
    if ad >= SCROLL_FOLLOW_ACTIVE_BONUS_GAP:
        if (delta > 0 and move_axis > 0) or (delta < 0 and move_axis < 0):
            step += SCROLL_FOLLOW_ACTIVE_BONUS

    base_ms = TARGET_FRAME_MS if TARGET_FRAME_MS > 0 else 20
    dt_mul = frame_dt // base_ms
    if dt_mul < 1:
        dt_mul = 1
    if dt_mul > SCROLL_FOLLOW_DT_MAX_SCALE:
        dt_mul = SCROLL_FOLLOW_DT_MAX_SCALE

    step *= dt_mul
    max_step = SCROLL_FOLLOW_MAX_PER_FRAME * dt_mul

    # After input stops, settle camera back to its target slightly faster.
    if move_axis == 0 and ad >= SCROLL_FOLLOW_FAST_GAP:
        max_step += SCROLL_SETTLE_BONUS
        step += SCROLL_SETTLE_BONUS

    if step > max_step:
        step = max_step

    if delta > 0:
        return min(scroll + step, target)
    return max(scroll - step, target)


def _calibrate_center(samples=24):
    sx = 0
    sy = 0
    axis_max = 4095
    for _ in range(samples):
        rx, mx = _adc_read(adc_x)
        ry, my = _adc_read(adc_y)
        sx += rx
        sy += ry
        axis_max = mx if mx > my else my
        time.sleep_ms(5)
    return sx // samples, sy // samples, axis_max


cx, cy, axis_max = _calibrate_center()
print("joystick center:", cx, cy, "max:", axis_max)
print("controls: move joystick, Ctrl-C to stop")

frame = 0
t0 = time.ticks_ms()

scroll_x = _clamp(player_x - ACTIVE_VIEW_W // 2, 0, world_w - ACTIVE_VIEW_W)
scroll_y = _clamp(player_y - ACTIVE_VIEW_H // 2, 0, world_h - ACTIVE_VIEW_H)
cam_margin_x = ACTIVE_VIEW_W // 4
cam_margin_y = ACTIVE_VIEW_H // 4
prev_scroll_x = scroll_x
prev_scroll_y = scroll_y
prev_player_x = player_x
prev_player_y = player_y
x_dir = 0
y_dir_raw = 0
anim_row = 0
anim_col = 1
anim_last_ms = time.ticks_ms()
face_right = False
move_carry_x = 0
move_carry_y = 0
prev_input_x = 0
prev_input_y = 0
prev_loop_ms = time.ticks_ms()
last_input_active_ms = prev_loop_ms
anim_x_dir = 0
anim_y_dir = 0
explore_moved = False
explore_scrolled = False
explore_anim_changed = False
explore_force_full_redraw = False
mode = MODE_EXPLORE
encounter_cooldown_frames = 0
act_dialog_until_ms = 0
fight_heart_x = battle_heart_init_x
fight_heart_y = battle_heart_init_y
battle_prev_heart_x = fight_heart_x
battle_prev_heart_y = fight_heart_y
battle_menu_dirty = True
battle_fight_dirty = True
battle_dialog_visible = False
battle_dialog_mode = 0
battle_heart_needs_sprite_refresh = False
fight_return_deadline_ms = 0
player_hp = PLAYER_HP_MAX
bullets = []
next_bullet_spawn_ms = 0
damage_invuln_until_ms = 0
battle_bullets_dirty = False
battle_prev_bullet_positions = []
battle_status_dirty = True
mercy_exit_pending = False
_rng_state = (time.ticks_ms() | 1) & 0x7FFFFFFF
interact_sw_prev = interact_sw.value()
btn_fight_prev = btn_fight.value()
btn_act_prev = btn_act.value()
btn_item_prev = btn_item.value()
btn_mercy_prev = btn_mercy.value()
leaf_zone_prev_inside = False
lamp_dialog_until_ms = 0
explore_overlay_dirty = False
current_map_id = MAP1_ID
teleport_cooldown_frames = 0

if player_sheet_enabled:
    lgfx.player_frame_set(anim_row * 3 + anim_col)
    if hasattr(lgfx, "player_flip_x_set"):
        lgfx.player_flip_x_set(face_right)

_render_scene(scroll_x, scroll_y, player_x, player_y, True)
if ENABLE_SPAWN_OVERLAY and hasattr(lgfx, "draw_png_file") and _path_exists(SPAWN_OVERLAY_PATH):
    lgfx.draw_png_file(
        SPAWN_OVERLAY_PATH,
        player_x - scroll_x - (PLAYER_FRAME_W // 2),
        player_y - scroll_y - (PLAYER_FRAME_H // 2),
        PLAYER_FRAME_W,
        PLAYER_FRAME_H,
    )
    time.sleep_ms(180)

def update_player(loop_start, frame_dt):
    global player_x, player_y, scroll_x, scroll_y
    global prev_input_x, prev_input_y, move_carry_x, move_carry_y
    global last_input_active_ms, anim_x_dir, anim_y_dir
    global anim_row, anim_col, anim_last_ms, face_right
    global explore_moved, explore_scrolled, explore_anim_changed
    global lamp_dialog_until_ms

    input_active = (x_dir != 0) or (y_dir_raw != 0)
    if input_active:
        last_input_active_ms = loop_start
        if x_dir != 0:
            anim_x_dir = x_dir
        if y_dir_raw != 0:
            anim_y_dir = y_dir_raw
    anim_active = input_active or (time.ticks_diff(loop_start, last_input_active_ms) < ANIM_IDLE_HOLD_MS)

    if x_dir == 0 or x_dir != prev_input_x:
        move_carry_x = 0
    if y_dir_raw == 0 or y_dir_raw != prev_input_y:
        move_carry_y = 0
    prev_input_x = x_dir
    prev_input_y = y_dir_raw

    dx, move_carry_x = _scaled_axis_delta(x_dir, MOVE_STEP, frame_dt, move_carry_x)
    dy_raw, move_carry_y = _scaled_axis_delta(y_dir_raw, MOVE_STEP, frame_dt, move_carry_y)

    # Typical joystick Y axis grows downward when pushed down.
    dy = -dy_raw

    player_x = _move_axis_with_collision(player_x, player_y, dx, True)
    player_y = _move_axis_with_collision(player_y, player_x, dy, False)

    move_dx = player_x - prev_player_x
    move_dy = player_y - prev_player_y

    desired_scroll_x = player_x - (ACTIVE_VIEW_W // 2)
    desired_scroll_y = player_y - (ACTIVE_VIEW_H // 2)

    # Keep small center deadband to avoid tiny camera wobble on joystick noise.
    sx = player_x - scroll_x
    sy = player_y - scroll_y
    center_x = ACTIVE_VIEW_W // 2
    center_y = ACTIVE_VIEW_H // 2
    if center_x - CAM_CENTER_DEADBAND_X <= sx <= center_x + CAM_CENTER_DEADBAND_X:
        desired_scroll_x = scroll_x
    if center_y - CAM_CENTER_DEADBAND_Y <= sy <= center_y + CAM_CENTER_DEADBAND_Y:
        desired_scroll_y = scroll_y
    target_scroll_x = _clamp(desired_scroll_x, 0, world_w - ACTIVE_VIEW_W)
    target_scroll_y = _clamp(desired_scroll_y, 0, world_h - ACTIVE_VIEW_H)

    # Keep camera target on coarse steps to reduce heavy tile scroll updates.
    target_scroll_x = (target_scroll_x // SCROLL_STEP) * SCROLL_STEP
    target_scroll_y = (target_scroll_y // SCROLL_STEP) * SCROLL_STEP

    if INSTANT_CAMERA_FOLLOW:
        scroll_x = target_scroll_x
        scroll_y = target_scroll_y
    else:
        scroll_x = _camera_chase_axis(scroll_x, target_scroll_x, move_dx, frame_dt)
        scroll_y = _camera_chase_axis(scroll_y, target_scroll_y, move_dy, frame_dt)

    # Hard camera guard: keep player away from viewport edges.
    sx = player_x - scroll_x
    if sx < CAM_HARD_LOCK_PAD:
        scroll_x = player_x - CAM_HARD_LOCK_PAD
    elif sx > ACTIVE_VIEW_W - 1 - CAM_HARD_LOCK_PAD:
        scroll_x = player_x - (ACTIVE_VIEW_W - 1 - CAM_HARD_LOCK_PAD)

    sy = player_y - scroll_y
    if sy < CAM_HARD_LOCK_PAD:
        scroll_y = player_y - CAM_HARD_LOCK_PAD
    elif sy > ACTIVE_VIEW_H - 1 - CAM_HARD_LOCK_PAD:
        scroll_y = player_y - (ACTIVE_VIEW_H - 1 - CAM_HARD_LOCK_PAD)

    scroll_x = _clamp(scroll_x, 0, world_w - ACTIVE_VIEW_W)
    scroll_y = _clamp(scroll_y, 0, world_h - ACTIVE_VIEW_H)

    # Freeze camera while dialog is visible to avoid full map redraw every step.
    if time.ticks_diff(lamp_dialog_until_ms, loop_start) > 0:
        scroll_x = prev_scroll_x
        scroll_y = prev_scroll_y

    explore_moved = (move_dx != 0) or (move_dy != 0)
    explore_scrolled = (scroll_x != prev_scroll_x) or (scroll_y != prev_scroll_y)

    if player_sheet_enabled:
        prev_face_right = face_right
        prev_anim_frame = anim_row * 3 + anim_col

        dir_x = x_dir if x_dir != 0 else anim_x_dir
        if dir_x > 0:
            face_right = True
        elif dir_x < 0:
            face_right = False

        if x_dir != 0 and y_dir_raw != 0:
            anim_row = PLAYER_ANIM_ROW_SIDE
        elif y_dir_raw != 0:
            anim_row = PLAYER_ANIM_ROW_FRONT
        elif x_dir != 0:
            anim_row = PLAYER_ANIM_ROW_SIDE

        if anim_active:
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, anim_last_ms) >= PLAYER_ANIM_STEP_MS:
                anim_last_ms = now_ms
                anim_col = (anim_col + 1) % 3
        else:
            anim_col = 1
            anim_last_ms = time.ticks_ms()

        if hasattr(lgfx, "player_flip_x_set"):
            lgfx.player_flip_x_set(face_right)
        new_anim_frame = anim_row * 3 + anim_col
        explore_anim_changed = (new_anim_frame != prev_anim_frame) or (face_right != prev_face_right)
        lgfx.player_frame_set(new_anim_frame)
    else:
        explore_anim_changed = False


def _draw_text_in_box(x, y, w, h, text):
    if not hasattr(lgfx, "draw_text"):
        return
    text_w = len(text) * 8
    tx = x + ((w - text_w) // 2)
    ty = y + ((h - 8) // 2)
    if tx < x + 2:
        tx = x + 2
    lgfx.draw_text(tx, ty, text, BATTLE_COLOR_WHITE)


def _draw_rect_thick(x, y, w, h, color, thickness):
    if w <= 0 or h <= 0:
        return
    if thickness < 1:
        thickness = 1
    t = thickness
    while t > 0:
        ox = thickness - t
        rw = w - (ox * 2)
        rh = h - (ox * 2)
        if rw <= 0 or rh <= 0:
            break
        lgfx.draw_rect(x + ox, y + ox, rw, rh, color)
        t -= 1


def _fill_rect_solid(x, y, w, h, color):
    if w <= 0 or h <= 0:
        return
    yy = y
    y_end = y + h
    while yy < y_end:
        lgfx.draw_rect(x, yy, w, 1, color)
        yy += 1


def _lamp_dialog_rect():
    dialog_w = 280
    if dialog_w > ACTIVE_VIEW_W - 8:
        dialog_w = ACTIVE_VIEW_W - 8
    dialog_h = 40
    dialog_x = (ACTIVE_VIEW_W - dialog_w) // 2
    dialog_y = ACTIVE_VIEW_H - dialog_h - 8
    if dialog_y < 4:
        dialog_y = 4
    return dialog_x, dialog_y, dialog_w, dialog_h


def _rects_intersect(ax, ay, aw, ah, bx, by, bw, bh):
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return False
    return not (
        (ax + aw) <= bx
        or (bx + bw) <= ax
        or (ay + ah) <= by
        or (by + bh) <= ay
    )


def _draw_explore_lamp_dialog(loop_start):
    dialog_active = time.ticks_diff(lamp_dialog_until_ms, loop_start) > 0
    if not dialog_active:
        return False

    dialog_x, dialog_y, dialog_w, dialog_h = _lamp_dialog_rect()

    # Fill full dialog with black to avoid seeing moving scene through the box.
    _fill_rect_solid(dialog_x, dialog_y, dialog_w, dialog_h, 0x0000)
    _draw_rect_thick(dialog_x, dialog_y, dialog_w, dialog_h, BATTLE_COLOR_WHITE, BATTLE_CMD_BORDER_THICK)

    text_drawn = False
    if hasattr(lgfx, "draw_png_file") and _path_exists(LAMP_DIALOG_TEXT_PATH):
        try:
            avail_w = dialog_w - 12
            avail_h = dialog_h - 8
            draw_w = LAMP_DIALOG_TEXT_W
            draw_h = LAMP_DIALOG_TEXT_H
            if draw_w > avail_w or draw_h > avail_h:
                # Keep aspect ratio when fitting to dialog.
                scale_w = (avail_w << 8) // LAMP_DIALOG_TEXT_W
                scale_h = (avail_h << 8) // LAMP_DIALOG_TEXT_H
                scale = scale_w if scale_w < scale_h else scale_h
                if scale < 1:
                    scale = 1
                draw_w = (LAMP_DIALOG_TEXT_W * scale) >> 8
                draw_h = (LAMP_DIALOG_TEXT_H * scale) >> 8
                if draw_w < 1:
                    draw_w = 1
                if draw_h < 1:
                    draw_h = 1
            text_x = dialog_x + ((dialog_w - draw_w) // 2)
            text_y = dialog_y + ((dialog_h - draw_h) // 2)
            text_drawn = bool(
                lgfx.draw_png_file(
                    LAMP_DIALOG_TEXT_PATH,
                    text_x,
                    text_y,
                    draw_w,
                    draw_h,
                )
            )
        except Exception:
            text_drawn = False
    if not text_drawn and hasattr(lgfx, "draw_text"):
        _draw_text_in_box(dialog_x + 4, dialog_y + 8, dialog_w - 8, dialog_h - 16, "三盞路燈合在一起真詭異")
    return True


def _draw_battle_frame():
    _draw_rect_thick(
        battle_frame_x,
        battle_frame_y,
        BATTLE_FRAME_W,
        BATTLE_FRAME_H,
        BATTLE_COLOR_WHITE,
        BATTLE_FRAME_BORDER_THICK,
    )


def _draw_battle_menu_screen(dialog_active):
    global battle_dialog_mode

    lgfx.clear()
    _draw_battle_frame()

    enemy_x = battle_frame_x + ((BATTLE_FRAME_W - ENEMY_SPRITE_W) // 2)
    enemy_y = battle_frame_y + 16
    enemy_bottom = enemy_y + ENEMY_SPRITE_H
    enemy_drawn = False
    if hasattr(lgfx, "draw_png_file") and _path_exists(ENEMY_SPRITE_PATH):
        enemy_drawn = bool(
            lgfx.draw_png_file(
                ENEMY_SPRITE_PATH,
                enemy_x,
                enemy_y,
                ENEMY_SPRITE_W,
                ENEMY_SPRITE_H,
            )
        )
    if not enemy_drawn:
        monster_cx = battle_frame_x + (BATTLE_FRAME_W // 2)
        monster_cy = battle_frame_y + 75
        lgfx.draw_circle(monster_cx, monster_cy, 22, BATTLE_COLOR_WHITE)
        enemy_bottom = monster_cy + 22

    for i, label in enumerate(("FIGHT", "ACT", "ITEM", "MERCY")):
        bx = battle_cmd_x0 + i * (battle_cmd_w + BATTLE_CMD_GAP)
        by = battle_cmd_y
        _draw_rect_thick(bx, by, battle_cmd_w, BATTLE_CMD_H, BATTLE_COLOR_WHITE, BATTLE_CMD_BORDER_THICK)
        _draw_text_in_box(bx, by, battle_cmd_w, BATTLE_CMD_H, label)

    if dialog_active:
        dialog_x = battle_frame_x + 10
        dialog_w = BATTLE_FRAME_W - 20
        dialog_h = 20
        dialog_y = enemy_bottom + 6
        max_dialog_y = battle_cmd_y - dialog_h - 6
        if dialog_y > max_dialog_y:
            dialog_y = max_dialog_y
        _draw_rect_thick(dialog_x, dialog_y, dialog_w, dialog_h, BATTLE_COLOR_WHITE, BATTLE_CMD_BORDER_THICK)
        if battle_dialog_mode == 2:
            mercy_text_drawn = False
            if hasattr(lgfx, "draw_png_file") and _path_exists(MERCY_DIALOG_TEXT_PATH):
                mercy_text_drawn = bool(
                    lgfx.draw_png_file(
                        MERCY_DIALOG_TEXT_PATH,
                        dialog_x + 6,
                        dialog_y + 3,
                        dialog_w - 12,
                        14,
                    )
                )
            if not mercy_text_drawn:
                if hasattr(lgfx, "draw_text"):
                    lgfx.draw_text(dialog_x + 8, dialog_y + 10, "MERCY...", BATTLE_COLOR_WHITE)
                else:
                    _draw_text_in_box(dialog_x, dialog_y + 6, dialog_w, 8, "MERCY...")
        else:
            dialog_text_drawn = False
            if hasattr(lgfx, "draw_png_file") and _path_exists(ACT_DIALOG_TEXT_PATH):
                dialog_text_drawn = bool(
                    lgfx.draw_png_file(
                        ACT_DIALOG_TEXT_PATH,
                        dialog_x + 6,
                        dialog_y + 3,
                        dialog_w - 12,
                        14,
                    )
                )
            if not dialog_text_drawn:
                _draw_text_in_box(dialog_x, dialog_y + 1, dialog_w, 8, "MONSTER LOOKS ANGRY!")
                if hasattr(lgfx, "draw_text"):
                    lgfx.draw_text(dialog_x + 8, dialog_y + 10, "ACT: MONSTER IS ANGRY!", BATTLE_COLOR_WHITE)


def _draw_battle_fight_background():
    lgfx.clear()
    _draw_battle_frame()


def _draw_battle_heart_sprite(cx, cy):
    if not hasattr(lgfx, "draw_png_file"):
        return False
    for path in (BATTLE_HEART_SPRITE_PATH, BATTLE_HEART_SPRITE_FALLBACK_PATH):
        if not _path_exists(path):
            continue
        if lgfx.draw_png_file(
            path,
            cx - (BATTLE_HEART_SPRITE_W // 2),
            cy - (BATTLE_HEART_SPRITE_H // 2),
            BATTLE_HEART_SPRITE_W,
            BATTLE_HEART_SPRITE_H,
        ):
            return True
    return False


def _rand_u32():
    global _rng_state
    _rng_state = ((_rng_state * 1103515245) + 12345) & 0x7FFFFFFF
    return _rng_state


def _rand_range(lo, hi):
    if hi <= lo:
        return lo
    span = hi - lo + 1
    return lo + (_rand_u32() % span)


def _battle_status_y():
    y = battle_frame_y + BATTLE_FRAME_H + 4
    max_y = ACTIVE_VIEW_H - 9
    if y > max_y:
        y = max_y
    return y


def _battle_status_y_menu():
    return battle_cmd_y - (8 + BATTLE_STATUS_TO_CMD_GAP)


def _reset_battle_state():
    global player_hp, bullets, next_bullet_spawn_ms, damage_invuln_until_ms
    global battle_bullets_dirty, battle_prev_bullet_positions, battle_status_dirty
    global fight_heart_x, fight_heart_y, battle_prev_heart_x, battle_prev_heart_y

    player_hp = PLAYER_HP_MAX
    bullets = []
    next_bullet_spawn_ms = 0
    damage_invuln_until_ms = 0
    battle_bullets_dirty = False
    battle_prev_bullet_positions = []
    battle_status_dirty = True
    fight_heart_x = battle_heart_init_x
    fight_heart_y = battle_heart_init_y
    battle_prev_heart_x = fight_heart_x
    battle_prev_heart_y = fight_heart_y


def _start_battle_from_explore():
    global mode, act_dialog_until_ms, battle_dialog_mode, mercy_exit_pending
    global battle_menu_dirty, battle_dialog_visible
    global explore_moved, explore_scrolled, explore_anim_changed
    global lamp_dialog_until_ms, explore_overlay_dirty

    mode = MODE_BATTLE_MENU
    act_dialog_until_ms = 0
    battle_dialog_mode = 0
    mercy_exit_pending = False
    battle_menu_dirty = True
    battle_dialog_visible = False
    lamp_dialog_until_ms = 0
    explore_overlay_dirty = False
    _reset_battle_state()
    print("battle_menu: Fight(GPIO38) Act(GPIO39) Item(GPIO40) Mercy(GPIO41)")
    explore_moved = False
    explore_scrolled = False
    explore_anim_changed = False


def _draw_battle_status_line(in_menu=False):
    if not hasattr(lgfx, "draw_text"):
        return
    text = "%s  HP %2d/%d" % (MONSTER_NAME, player_hp, PLAYER_HP_MAX)
    x = battle_frame_x + 12
    if in_menu:
        y = _battle_status_y_menu()
    else:
        y = _battle_status_y()
    # Simulate a slightly larger/bolder look using 2x2 overdraw.
    lgfx.draw_text(x, y, text, BATTLE_COLOR_WHITE)
    lgfx.draw_text(x + 1, y, text, BATTLE_COLOR_WHITE)
    lgfx.draw_text(x, y + 1, text, BATTLE_COLOR_WHITE)
    lgfx.draw_text(x + 1, y + 1, text, BATTLE_COLOR_WHITE)


def _get_bullet_positions():
    out = []
    for b in bullets:
        out.append((b[0] >> BULLET_FP_SHIFT, b[1] >> BULLET_FP_SHIFT))
    return out


def _erase_prev_bullets():
    for x, y in battle_prev_bullet_positions:
        lgfx.draw_circle(x, y, BULLET_R, 0x0000)


def _spawn_bullet_random_edge(now_ms):
    global next_bullet_spawn_ms, bullets

    if time.ticks_diff(now_ms, next_bullet_spawn_ms) < 0:
        return False

    inner_inset = BATTLE_FRAME_BORDER_THICK
    if BATTLE_BORDER_THICK > inner_inset:
        inner_inset = BATTLE_BORDER_THICK
    inner_min_x = battle_frame_x + inner_inset + BULLET_R
    inner_max_x = battle_frame_x + BATTLE_FRAME_W - inner_inset - BULLET_R - 1
    inner_min_y = battle_frame_y + inner_inset + BULLET_R
    inner_max_y = battle_frame_y + BATTLE_FRAME_H - inner_inset - BULLET_R - 1

    edge = _rand_u32() & 0x03
    if edge == 0:
        sx = _rand_range(inner_min_x, inner_max_x)
        sy = inner_min_y
    elif edge == 1:
        sx = _rand_range(inner_min_x, inner_max_x)
        sy = inner_max_y
    elif edge == 2:
        sx = inner_min_x
        sy = _rand_range(inner_min_y, inner_max_y)
    else:
        sx = inner_max_x
        sy = _rand_range(inner_min_y, inner_max_y)

    tx = _rand_range(inner_min_x, inner_max_x)
    ty = _rand_range(inner_min_y, inner_max_y)
    dx = tx - sx
    dy = ty - sy
    scale = abs(dx)
    if abs(dy) > scale:
        scale = abs(dy)
    if scale <= 0:
        vx_fp = 1 << BULLET_FP_SHIFT
        vy_fp = 0
    else:
        vx_fp = (dx << BULLET_FP_SHIFT) // scale
        vy_fp = (dy << BULLET_FP_SHIFT) // scale
        if vx_fp == 0 and vy_fp == 0:
            vx_fp = 1 << BULLET_FP_SHIFT

    bullets.append([sx << BULLET_FP_SHIFT, sy << BULLET_FP_SHIFT, vx_fp, vy_fp])
    next_bullet_spawn_ms = time.ticks_add(now_ms, BULLET_SPAWN_INTERVAL_MS)
    return True


def _update_bullets_and_collisions(now_ms):
    global bullets, player_hp, damage_invuln_until_ms
    global mode, encounter_cooldown_frames, act_dialog_until_ms, explore_force_full_redraw
    global battle_menu_dirty, battle_dialog_visible, battle_status_dirty
    global battle_dialog_mode, mercy_exit_pending

    inner_inset = BATTLE_FRAME_BORDER_THICK
    if BATTLE_BORDER_THICK > inner_inset:
        inner_inset = BATTLE_BORDER_THICK
    inner_min_x = battle_frame_x + inner_inset + BULLET_R
    inner_max_x = battle_frame_x + BATTLE_FRAME_W - inner_inset - BULLET_R - 1
    inner_min_y = battle_frame_y + inner_inset + BULLET_R
    inner_max_y = battle_frame_y + BATTLE_FRAME_H - inner_inset - BULLET_R - 1
    hit_r = BATTLE_HEART_HIT_R + BULLET_R
    hit_r2 = hit_r * hit_r
    can_take_damage = time.ticks_diff(now_ms, damage_invuln_until_ms) >= 0
    changed = False
    kept = []

    for b in bullets:
        b[0] += b[2] * BULLET_SPEED_PX
        b[1] += b[3] * BULLET_SPEED_PX
        bx = b[0] >> BULLET_FP_SHIFT
        by = b[1] >> BULLET_FP_SHIFT
        if bx < inner_min_x or bx > inner_max_x or by < inner_min_y or by > inner_max_y:
            changed = True
            continue

        dx = bx - fight_heart_x
        dy = by - fight_heart_y
        if can_take_damage and (dx * dx + dy * dy) <= hit_r2:
            player_hp -= 1
            battle_status_dirty = True
            damage_invuln_until_ms = time.ticks_add(now_ms, DAMAGE_INVULN_MS)
            can_take_damage = False
            changed = True
            if player_hp <= 0:
                mode = MODE_EXPLORE
                encounter_cooldown_frames = ENCOUNTER_COOLDOWN_FRAMES
                act_dialog_until_ms = 0
                battle_dialog_mode = 0
                mercy_exit_pending = False
                explore_force_full_redraw = True
                battle_menu_dirty = True
                battle_dialog_visible = False
                bullets = []
                return True
            continue

        kept.append(b)
        changed = True

    if len(kept) != len(bullets):
        changed = True
    bullets = kept
    return changed


def _draw_bullets():
    for b in bullets:
        lgfx.draw_circle(
            b[0] >> BULLET_FP_SHIFT,
            b[1] >> BULLET_FP_SHIFT,
            BULLET_R,
            BATTLE_COLOR_WHITE,
        )


def update_battle_menu(loop_start, fight_pressed, act_pressed, item_pressed, mercy_pressed):
    global mode, encounter_cooldown_frames, act_dialog_until_ms
    global battle_dialog_mode, mercy_exit_pending
    global explore_force_full_redraw, fight_heart_x, fight_heart_y
    global battle_menu_dirty, battle_fight_dirty, battle_heart_needs_sprite_refresh, fight_return_deadline_ms

    dialog_active = time.ticks_diff(act_dialog_until_ms, loop_start) > 0
    if mercy_exit_pending and not dialog_active:
        mode = MODE_EXPLORE
        encounter_cooldown_frames = ENCOUNTER_COOLDOWN_FRAMES
        act_dialog_until_ms = 0
        battle_dialog_mode = 0
        mercy_exit_pending = False
        explore_force_full_redraw = True
        battle_menu_dirty = True
        return
    if dialog_active:
        return

    if fight_pressed:
        mode = MODE_BATTLE_FIGHT
        fight_heart_x = battle_heart_init_x
        fight_heart_y = battle_heart_init_y
        battle_fight_dirty = True
        battle_heart_needs_sprite_refresh = False
        fight_return_deadline_ms = time.ticks_add(loop_start, FIGHT_AUTO_RETURN_MS)
        print("FIGHT")
        return
    if act_pressed:
        print("ACT: 怪物看起來很生氣！")
        act_dialog_until_ms = time.ticks_add(loop_start, ACT_DIALOG_MS)
        battle_dialog_mode = 1
        mercy_exit_pending = False
        battle_menu_dirty = True
        return
    if item_pressed:
        print("ITEM")
        return
    if mercy_pressed:
        print("MERCY: 多麼的無聊!")
        act_dialog_until_ms = time.ticks_add(loop_start, MERCY_DIALOG_MS)
        battle_dialog_mode = 2
        mercy_exit_pending = True
        battle_menu_dirty = True


def update_battle_fight(loop_start):
    global mode, fight_heart_x, fight_heart_y
    global battle_menu_dirty, battle_dialog_visible, fight_return_deadline_ms
    global battle_fight_dirty, battle_bullets_dirty, battle_status_dirty
    global battle_dialog_mode, mercy_exit_pending
    global bullets, next_bullet_spawn_ms, damage_invuln_until_ms, battle_prev_bullet_positions

    if time.ticks_diff(fight_return_deadline_ms, loop_start) <= 0:
        mode = MODE_BATTLE_MENU
        battle_menu_dirty = True
        battle_dialog_visible = False
        bullets = []
        next_bullet_spawn_ms = 0
        damage_invuln_until_ms = 0
        battle_prev_bullet_positions = []
        battle_bullets_dirty = False
        battle_status_dirty = True
        battle_dialog_mode = 0
        mercy_exit_pending = False
        return

    if x_dir > 0:
        fight_heart_x += BATTLE_HEART_STEP
    elif x_dir < 0:
        fight_heart_x -= BATTLE_HEART_STEP

    if y_dir_raw > 0:
        fight_heart_y -= BATTLE_HEART_STEP
    elif y_dir_raw < 0:
        fight_heart_y += BATTLE_HEART_STEP

    fight_heart_x = _clamp(fight_heart_x, battle_heart_min_x, battle_heart_max_x)
    fight_heart_y = _clamp(fight_heart_y, battle_heart_min_y, battle_heart_max_y)

    spawned = _spawn_bullet_random_edge(loop_start)
    changed = _update_bullets_and_collisions(loop_start)
    if mode != MODE_BATTLE_FIGHT:
        return
    battle_bullets_dirty = spawned or changed or bool(bullets)


def draw_all(loop_start):
    global prev_player_x, prev_player_y, prev_scroll_x, prev_scroll_y
    global explore_force_full_redraw, explore_overlay_dirty
    global battle_prev_heart_x, battle_prev_heart_y
    global battle_menu_dirty, battle_fight_dirty, battle_dialog_visible, battle_heart_needs_sprite_refresh
    global battle_bullets_dirty, battle_prev_bullet_positions
    global battle_status_dirty

    if mode == MODE_EXPLORE:
        scene_redrawn = False
        player_redrawn = False
        if explore_force_full_redraw:
            _render_scene(scroll_x, scroll_y, player_x, player_y, True)
            explore_force_full_redraw = False
            scene_redrawn = True
        elif explore_scrolled:
            _render_scene(scroll_x, scroll_y, player_x, player_y, FORCE_FULL_REDRAW_WHEN_SCROLLED)
            scene_redrawn = True
        elif explore_moved or explore_anim_changed:
            lgfx.draw_player(player_x - scroll_x, player_y - scroll_y, PLAYER_COLOR, PLAYER_R)
            player_redrawn = True

        dialog_active = time.ticks_diff(lamp_dialog_until_ms, loop_start) > 0
        dialog_needs_redraw = False
        if dialog_active:
            if not explore_overlay_dirty:
                dialog_needs_redraw = True
            elif scene_redrawn:
                dialog_needs_redraw = True
            elif player_redrawn:
                dialog_x, dialog_y, dialog_w, dialog_h = _lamp_dialog_rect()
                if player_sheet_enabled:
                    half_w = PLAYER_FRAME_W // 2
                    half_h = PLAYER_FRAME_H // 2
                else:
                    half_w = PLAYER_R
                    half_h = PLAYER_R
                px = player_x - scroll_x - half_w
                py = player_y - scroll_y - half_h
                pw = half_w * 2 + 1
                ph = half_h * 2 + 1
                if _rects_intersect(px, py, pw, ph, dialog_x, dialog_y, dialog_w, dialog_h):
                    dialog_needs_redraw = True

        if dialog_needs_redraw:
            if _draw_explore_lamp_dialog(loop_start):
                explore_overlay_dirty = True
        elif not dialog_active and explore_overlay_dirty:
            # Dialog just ended; redraw scene next frame to clear overlay remnants.
            explore_force_full_redraw = True
            explore_overlay_dirty = False
        prev_player_x = player_x
        prev_player_y = player_y
        prev_scroll_x = scroll_x
        prev_scroll_y = scroll_y
        return

    if mode == MODE_BATTLE_MENU:
        dialog_active = time.ticks_diff(act_dialog_until_ms, loop_start) > 0
        if battle_menu_dirty or dialog_active != battle_dialog_visible:
            _draw_battle_menu_screen(dialog_active)
            battle_menu_dirty = False
            battle_dialog_visible = dialog_active
        if not dialog_active:
            _draw_battle_status_line(True)
        return

    moved = (fight_heart_x != battle_prev_heart_x) or (fight_heart_y != battle_prev_heart_y)
    can_draw_png = hasattr(lgfx, "draw_png_file")

    if not battle_fight_dirty and not moved and not battle_bullets_dirty and not battle_status_dirty:
        return

    if battle_fight_dirty:
        _draw_battle_fight_background()
        _draw_bullets()
    else:
        if battle_bullets_dirty:
            _erase_prev_bullets()
            _draw_bullets()
        if moved:
            lgfx.draw_circle(battle_prev_heart_x, battle_prev_heart_y, BATTLE_HEART_ERASE_R, 0x0000)

    heart_drawn = _draw_battle_heart_sprite(fight_heart_x, fight_heart_y) if can_draw_png else False
    if not heart_drawn:
        lgfx.draw_circle(fight_heart_x, fight_heart_y, BATTLE_HEART_FAST_R, BATTLE_COLOR_RED)

    # Repaint border after local erase paths so edge pixels remain stable.
    _draw_battle_frame()
    if battle_status_dirty or battle_fight_dirty:
        _draw_battle_status_line()
        battle_status_dirty = False
    battle_heart_needs_sprite_refresh = False

    battle_prev_heart_x = fight_heart_x
    battle_prev_heart_y = fight_heart_y
    battle_prev_bullet_positions = _get_bullet_positions()
    battle_bullets_dirty = False
    battle_fight_dirty = False


while True:
    loop_start = time.ticks_ms()
    frame_dt = time.ticks_diff(loop_start, prev_loop_ms)
    if frame_dt <= 0:
        frame_dt = TARGET_FRAME_MS if TARGET_FRAME_MS > 0 else 20
    prev_loop_ms = loop_start

    frame += 1
    if encounter_cooldown_frames > 0:
        encounter_cooldown_frames -= 1
    if teleport_cooldown_frames > 0:
        teleport_cooldown_frames -= 1

    rx, _ = _adc_read_avg(adc_x, ADC_SAMPLES)
    ry, _ = _adc_read_avg(adc_y, ADC_SAMPLES)
    x_dir = _axis_dir(rx, cx, axis_max, x_dir)
    y_dir_raw = _axis_dir(ry, cy, axis_max, y_dir_raw)

    interact_sw_prev, interact_pressed = _read_falling_edge(interact_sw, interact_sw_prev)
    btn_fight_prev, fight_pressed = _read_falling_edge(btn_fight, btn_fight_prev)
    btn_act_prev, act_pressed = _read_falling_edge(btn_act, btn_act_prev)
    btn_item_prev, item_pressed = _read_falling_edge(btn_item, btn_item_prev)
    btn_mercy_prev, mercy_pressed = _read_falling_edge(btn_mercy, btn_mercy_prev)

    if mode == MODE_EXPLORE:
        update_player(loop_start, frame_dt)

        if teleport_cooldown_frames == 0:
            if current_map_id == MAP1_ID and _in_rect(player_x, player_y, MAP1_PORTAL_TO_MAP2_RECT_PX):
                switch_map(MAP2_ID)
            elif current_map_id == MAP2_ID and _in_rect(player_x, player_y, MAP2_PORTAL_TO_MAP1_RECT_PX):
                switch_map(MAP1_ID)

        if mode == MODE_EXPLORE and current_map_id == MAP1_ID:
            leaf_inside = _in_rect(player_x, player_y, LEAF_BATTLE_RECT_PX)
            if (not leaf_zone_prev_inside) and leaf_inside and encounter_cooldown_frames == 0:
                _start_battle_from_explore()
            leaf_zone_prev_inside = leaf_inside
        else:
            leaf_zone_prev_inside = False

        if mode == MODE_EXPLORE and current_map_id == MAP1_ID and interact_pressed and _in_rect(player_x, player_y, LAMP_INTERACT_RECT_PX):
            lamp_dialog_until_ms = time.ticks_add(loop_start, LAMP_DIALOG_MS)
            # Mark as not drawn yet so the dialog appears immediately this frame.
            explore_overlay_dirty = False
    elif mode == MODE_BATTLE_MENU:
        explore_moved = False
        explore_scrolled = False
        explore_anim_changed = False
        update_battle_menu(loop_start, fight_pressed, act_pressed, item_pressed, mercy_pressed)
    else:
        explore_moved = False
        explore_scrolled = False
        explore_anim_changed = False
        update_battle_fight(loop_start)

    draw_all(loop_start)

    if frame % 120 == 0:
        gc.collect()
        dt = time.ticks_diff(time.ticks_ms(), t0)
        fps = (frame * 1000 / dt) if dt else 0
        print("frame", frame, "fps", fps, "mode", mode, "cooldown", encounter_cooldown_frames, "stats", lgfx.stats(), "mem_free", gc.mem_free())

    if mode == MODE_EXPLORE and not explore_moved and not explore_scrolled:
        time.sleep_ms(1)
    if TARGET_FRAME_MS > 0:
        frame_used = time.ticks_diff(time.ticks_ms(), loop_start)
        if frame_used < TARGET_FRAME_MS:
            time.sleep_ms(TARGET_FRAME_MS - frame_used)
