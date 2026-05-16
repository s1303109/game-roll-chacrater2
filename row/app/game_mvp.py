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


def _resolve_asset_base(base_list):
    for base in base_list:
        if base.startswith("/sd/") and not SD_READY:
            continue
        if _path_exists(base + "/map.json"):
            return base
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


def _resolve_first_existing_path(paths):
    for path in paths:
        if path and _path_exists(path):
            return path
    return None


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


def _load_tiles(meta, base, tile, map_w, map_h, prefer_stream=False):
    meta_endian = meta.get("endian", "little")
    if meta_endian not in ("little", "big"):
        raise RuntimeError("TILE_ENDIAN_UNSUPPORTED")

    err = _validate_tile_files(base, tile, map_w, map_h)
    if err:
        raise RuntimeError(err)

    tilemap_path = base + "/tilemap.bin"
    tileset_path = base + "/tileset.bin"
    def _tile_load_error_code():
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
        return code

    def _can_stream():
        if meta_endian != "little":
            return False
        if not hasattr(lgfx, "tile_load_files"):
            return False
        if hasattr(lgfx, "tile_loader_mode"):
            try:
                mode = lgfx.tile_loader_mode()
            except Exception:
                return False
            if mode != 2:
                print("tile_loader_stream_skip_mode:", mode)
                return False
        return True

    def _try_stream():
        if not _can_stream():
            return False, "STREAM_UNAVAILABLE"
        if lgfx.tile_load_files(tileset_path, tilemap_path):
            print("tile_loader: stream")
            return True, None
        return False, _tile_load_error_code()

    def _try_memory():
        gc.collect()
        try:
            tileset = _read_file(tileset_path)
            tilemap = _read_file(tilemap_path)
            if meta_endian == "big":
                tileset = _swap16(tileset)
                tilemap = _swap16(tilemap)
            if lgfx.tile_load(tileset, tilemap):
                print("tile_loader: memory")
                return True, None
            print("tile_loader_memory_fail")
            return False, _tile_load_error_code()
        except MemoryError:
            print("tile_loader_memory_oom mem_free:", gc.mem_free())
            return False, "TILE_OOM"

    if prefer_stream:
        ok, stream_err = _try_stream()
        if ok:
            return "little"
        if stream_err not in ("STREAM_UNAVAILABLE", None):
            print("tile_loader_stream_fail:", stream_err)
        print("tile_loader_stream_fallback_memory")
        ok, mem_err = _try_memory()
        if ok:
            return "little"
        raise RuntimeError(mem_err if mem_err else "TILE_LOAD_FAIL")

    ok, mem_err = _try_memory()
    if ok:
        return "little"

    ok, stream_err = _try_stream()
    if ok:
        return "little"
    if stream_err not in ("STREAM_UNAVAILABLE", None):
        raise RuntimeError(stream_err)
    raise RuntimeError(mem_err if mem_err else "TILE_OOM")


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
SPAWN_OVERLAY_PATH = "/main character close eyes.orig.png"
ENABLE_SPAWN_INTRO = True
SPAWN_SPOTLIGHT_RADIUS = 56
SPAWN_OVERLAY_PATHS = (
    "/workspace/main character close eyes.clean.png",
    "/main character close eyes.clean.png",
    "/workspace/main character close eyes.orig.png",
    "/main character close eyes.orig.png",
)
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
MODE_EXPLORE_INVENTORY = 3
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
BATTLE_CMD_COLOR = 0xFC60  # #FF8C00 in RGB565
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
ACT_OPT1_PNG = "/act_opt1_text.png"
ACT_OPT2_PNG = "/act_opt2_text.png"
ACT_OPT3_PNG = "/act_opt3_text.png"
ACT_REPLY1_PNG = "/act_reply1_text.png"
ACT_REPLY2_PNG = "/act_reply2_text.png"
ACT_REPLY3_PNG = "/act_reply3_text.png"
MERCY_LOCKED_PNG = "/mercy_locked_text.png"
CMD_ICON_SRC_W = 32
CMD_ICON_SRC_H = 32
STAR_ICON_SRC_W = 24
STAR_ICON_SRC_H = 24
STAR_ICON_PATHS = ("/workspace/star_icon_24.png", "/star_icon_24.png", "/workspace/STAR .png", "/STAR .png")
INVENTORY_PORTRAIT_PATHS = (
    "/inventory_portrait.png",
    "/workspace/inventory_portrait.png",
    "/image.png",
    "/workspace/image.png",
)
INVENTORY_PORTRAIT_SRC_W = 255
INVENTORY_PORTRAIT_SRC_H = 221
FIGHT_ICON_PATHS = ("/workspace/fight_icon.png", "/fight_icon.png")
ACT_ICON_PATHS = ("/workspace/act_icon.png", "/act_icon.png")
ITEM_ICON_PATHS = ("/workspace/item_icon.png", "/item_icon.png")
MERCY_ICON_PATHS = ("/workspace/mercy_icon.png", "/mercy_icon.png")
CMD_ICON_PATHS = (
    FIGHT_ICON_PATHS,
    ACT_ICON_PATHS,
    ITEM_ICON_PATHS,
    MERCY_ICON_PATHS,
)
ACT_OPTION_PNG_INFOS = (
    (ACT_OPT1_PNG, 88, 18),
    (ACT_OPT2_PNG, 72, 18),
    (ACT_OPT3_PNG, 64, 18),
)
ACT_REPLY_PNG_INFOS = (
    (ACT_REPLY1_PNG, 132, 18),
    (ACT_REPLY2_PNG, 168, 18),
    (ACT_REPLY3_PNG, 132, 18),
)
MERCY_LOCKED_PNG_INFO = (MERCY_LOCKED_PNG, 144, 18)
MERCY_SUCCESS_PNG_INFO = (MERCY_DIALOG_TEXT_PATH, 220, 20)
ACT_REPLY_MS = 1000
BATTLE_DIALOG_NONE = 0
BATTLE_DIALOG_ACT_OPTIONS = 1
BATTLE_DIALOG_ACT_REPLY = 2
BATTLE_DIALOG_MERCY_LOCKED = 3
BATTLE_DIALOG_MERCY_EXIT = 4
BATTLE_DIALOG_ITEM_RESULT = 5
LEAF_BATTLE_RECT_PX = (128, 304, 96, 64)
# Expand to cover the full triple-lamp poles and nearby interaction area.
LAMP_INTERACT_RECT_PX = (160, 624, 128, 192)
MAP1_ID = 1
MAP2_ID = 2
MAP1_SPAWN_OFFSET_X = 0
MAP1_SPAWN_OFFSET_Y = -63
MAP2_LOCAL_ASSET_BASE = "/out_map2"
MAP2_ASSET_BASE = "/sd/out_map2"
MAP2_REMOTE_ASSET_BASE = "/remote/assets/out_map2"
MAP2_ASSET_BASES = (MAP2_LOCAL_ASSET_BASE, MAP2_ASSET_BASE, MAP2_REMOTE_ASSET_BASE)
MAP1_PORTAL_TO_MAP2_RECT_PX = (304, 160, 32, 96)
MAP2_PORTAL_TO_MAP1_RECT_PX = (96, 200, 38, 60)
PRELOAD_PORTAL_PAD_PX = 32
TELEPORT_COOLDOWN_FRAMES = 30
LAMP_DIALOG_TEXT_W = 214
LAMP_DIALOG_TEXT_H = 27
ACT_DIALOG_MS = 1000
MERCY_DIALOG_MS = 2500
LAMP_DIALOG_MS = 2000
ITEM_REPLY_MS = 1000
PLAYER_HP_MAX = 20
PLAYER_NAME = "OTIS"
PLAYER_LV = 1
PLAYER_WEAPON = "Stick"
PLAYER_ARMOR = "Bandage"
PLAYER_AT_BASE = 0
PLAYER_AT_BONUS = 0
PLAYER_DF_BASE = 0
PLAYER_DF_BONUS = 0
INVENTORY_CAPACITY = 8
MONSTER_NAME = "Grim Reaper"
BULLET_R = 3
BULLET_SPEED_PX = 2
BULLET_SPAWN_INTERVAL_MS = 300
DAMAGE_INVULN_MS = 450
BULLET_FP_SHIFT = 8
BATTLE_STATUS_TO_CMD_GAP = 2
BATTLE_HP_BAR_W = 36
BATTLE_HP_BAR_H = 6
BATTLE_HP_BAR_GAP = 5
BATTLE_HP_BAR_FILL_COLOR = 0xFC60  # deep orange
BATTLE_HP_BAR_EMPTY_COLOR = 0xF800  # red
BATTLE_HP_NAME_TO_HP_GAP = 22
FIGHT_AUTO_RETURN_MS = 7000
BUILD_TAG = "game_mvp_tune29_heart_sprite_io_tune_20260502"

print("build:", BUILD_TAG)

MAP_REGISTRY = {
    MAP1_ID: {
        "asset_bases": ASSET_BASES,
        "prefer_stream": False,
        "portals": (
            {"rect": MAP1_PORTAL_TO_MAP2_RECT_PX, "target_map_id": MAP2_ID},
        ),
    },
    MAP2_ID: {
        "asset_bases": MAP2_ASSET_BASES,
        "prefer_stream": True,
        "portals": (
            {"rect": MAP2_PORTAL_TO_MAP1_RECT_PX, "target_map_id": MAP1_ID},
        ),
    },
}

preload_cache = None

ITEM_HEAL_TEST = {
    "id": "heal_candy",
    "name": "Candy",
    "heal_amount": 6,
    "consumable": True,
}

inventory_items = [
    {
        "id": ITEM_HEAL_TEST["id"],
        "name": ITEM_HEAL_TEST["name"],
        "heal_amount": ITEM_HEAL_TEST["heal_amount"],
        "consumable": ITEM_HEAL_TEST["consumable"],
    },
    {
        "id": ITEM_HEAL_TEST["id"],
        "name": ITEM_HEAL_TEST["name"],
        "heal_amount": ITEM_HEAL_TEST["heal_amount"],
        "consumable": ITEM_HEAL_TEST["consumable"],
    },
]


def _inventory_clone_item(item):
    if not item:
        return None
    return {
        "id": item.get("id", "item"),
        "name": item.get("name", "Item"),
        "heal_amount": int(item.get("heal_amount", 0)),
        "consumable": bool(item.get("consumable", True)),
    }


def inventory_is_empty():
    return len(inventory_items) == 0


def inventory_try_add(item):
    if len(inventory_items) >= INVENTORY_CAPACITY:
        return False
    cloned = _inventory_clone_item(item)
    if not cloned:
        return False
    inventory_items.append(cloned)
    return True


def inventory_remove_at(index):
    if index < 0 or index >= len(inventory_items):
        return None
    return inventory_items.pop(index)


def inventory_clamp_index(index):
    count = len(inventory_items)
    if count <= 0:
        return 0
    if index < 0:
        return 0
    if index >= count:
        return count - 1
    return index


def _apply_spawn_offset_for_map(map_id, sx, sy):
    if map_id == MAP1_ID:
        return sx + MAP1_SPAWN_OFFSET_X, sy + MAP1_SPAWN_OFFSET_Y
    return sx, sy

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
spawn_x, spawn_y = _apply_spawn_offset_for_map(MAP1_ID, spawn_x, spawn_y)
player_x = spawn_x
player_y = spawn_y

if not DISPLAY_INIT_DONE:
    lgfx.init()
    DISPLAY_INIT_DONE = True
lgfx.set_rotation(ROTATION)
if hasattr(lgfx, "tile_loader_mode"):
    try:
        print("tile_loader_mode:", lgfx.tile_loader_mode())
    except Exception as err:
        print("tile_loader_mode_error:", err)
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

runtime_endian = _load_tiles(meta, asset_base, tile, map_w, map_h, prefer_stream=False)
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


def _nearest_walkable(px, py, max_radius=160):
    # If the requested spawn is already valid, keep it untouched.
    if not _collides(px, py, PLAYER_R):
        return px, py

    # Search outward in a diamond ring so the closest valid point is preferred.
    for r in range(1, max_radius + 1):
        # top/bottom edges
        for dx in range(-r, r + 1):
            for dy in (-r, r):
                nx = _clamp(px + dx, PLAYER_R, world_w - PLAYER_R - 1)
                ny = _clamp(py + dy, PLAYER_R, world_h - PLAYER_R - 1)
                if not _collides(nx, ny, PLAYER_R):
                    return nx, ny
        # left/right edges (excluding corners already checked above)
        for dy in range(-r + 1, r):
            for dx in (-r, r):
                nx = _clamp(px + dx, PLAYER_R, world_w - PLAYER_R - 1)
                ny = _clamp(py + dy, PLAYER_R, world_h - PLAYER_R - 1)
                if not _collides(nx, ny, PLAYER_R):
                    return nx, ny

    # Fallback: keep current value even if blocked; caller can still clamp/use it.
    return px, py


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

# Keep startup robust when map metadata spawn lands inside a blocked tile.
safe_start_x, safe_start_y = _nearest_walkable(player_x, player_y)
if safe_start_x != player_x or safe_start_y != player_y:
    print("startup_spawn_adjusted:", player_x, player_y, "->", safe_start_x, safe_start_y)
player_x, player_y = safe_start_x, safe_start_y


def _load_map_context(base, fallback_all_walkable=False, prefer_stream=False, preloaded_meta=None, preloaded_collision=None):
    global asset_base, meta, tile, map_w, map_h, world_w, world_h, runtime_endian, collision

    phase = {
        "map_json_ms": 0,
        "tile_setup_ms": 0,
        "tile_load_ms": 0,
        "collision_load_ms": 0,
    }

    t0 = time.ticks_ms()
    try:
        if preloaded_meta is None:
            with open(base + "/map.json", "r") as f:
                new_meta = json.loads(f.read())
            _validate_meta(new_meta)
        else:
            new_meta = preloaded_meta
            _validate_meta(new_meta)
    except Exception as err:
        raise RuntimeError("map_json:%s" % err)
    phase["map_json_ms"] = time.ticks_diff(time.ticks_ms(), t0)

    asset_base = base
    meta = new_meta
    tile = meta["tile_size"]
    map_w = meta["map_w"]
    map_h = meta["map_h"]
    world_w = map_w * tile
    world_h = map_h * tile

    t0 = time.ticks_ms()
    try:
        _tile_setup_with_fallback()
    except Exception as err:
        raise RuntimeError("tile_setup:%s" % err)
    phase["tile_setup_ms"] = time.ticks_diff(time.ticks_ms(), t0)

    t0 = time.ticks_ms()
    try:
        runtime_endian = _load_tiles(meta, asset_base, tile, map_w, map_h, prefer_stream=prefer_stream)
    except Exception as err:
        raise RuntimeError("tile_load:%s" % err)
    phase["tile_load_ms"] = time.ticks_diff(time.ticks_ms(), t0)
    if hasattr(lgfx, "set_swap_bytes"):
        lgfx.set_swap_bytes(runtime_endian == "little")

    t0 = time.ticks_ms()
    try:
        collision_data = preloaded_collision
        collision_err = None
        if collision_data is not None and len(collision_data) != map_w * map_h:
            raise RuntimeError("PRELOAD_COLLISION_SIZE_MISMATCH")
        if collision_data is None:
            collision_data, collision_err = _load_collision(meta, asset_base, map_w, map_h)
    except Exception as err:
        raise RuntimeError("collision_load:%s" % err)
    phase["collision_load_ms"] = time.ticks_diff(time.ticks_ms(), t0)

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
    return phase


def switch_map(target_map_id, spawn_x=None, spawn_y=None):
    global collision, meta, asset_base, current_map_id
    global player_x, player_y, scroll_x, scroll_y
    global prev_scroll_x, prev_scroll_y, prev_player_x, prev_player_y
    global leaf_zone_prev_inside, explore_overlay_dirty, lamp_dialog_until_ms
    global explore_force_full_redraw, teleport_cooldown_frames
    global tile, map_w, map_h, world_w, world_h, runtime_endian
    global preload_cache

    phase = {
        "resolve_base_ms": 0,
        "map_json_ms": 0,
        "tile_setup_ms": 0,
        "tile_load_ms": 0,
        "collision_load_ms": 0,
        "spawn_finalize_ms": 0,
    }
    fail_stage = None
    total_start = time.ticks_ms()

    def _print_switch_timings():
        print("resolve_base_ms:", phase["resolve_base_ms"])
        print("map_json_ms:", phase["map_json_ms"])
        print("tile_setup_ms:", phase["tile_setup_ms"])
        print("tile_load_ms:", phase["tile_load_ms"])
        print("collision_load_ms:", phase["collision_load_ms"])
        print("spawn_finalize_ms:", phase["spawn_finalize_ms"])
        print("switch_map_ms_total:", time.ticks_diff(time.ticks_ms(), total_start))

    config = MAP_REGISTRY.get(target_map_id)
    if not config:
        print("switch_map_fail_stage:resolve_base")
        _print_switch_timings()
        _release_preload_cache("switch_fail")
        teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
        return False

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

    fallback_all_walkable = False
    next_base = None
    next_meta = None
    preloaded_collision = None
    prefer_stream = bool(config.get("prefer_stream", False))

    use_preload = (
        preload_cache is not None
        and preload_cache.get("source_map_id") == current_map_id
        and preload_cache.get("target_map_id") == target_map_id
    )
    if use_preload:
        next_base = preload_cache.get("base")
        next_meta = preload_cache.get("meta")
        preloaded_collision = preload_cache.get("collision")
        prefer_stream = bool(preload_cache.get("prefer_stream", prefer_stream))
        cached_spawn = preload_cache.get("spawn")
        if spawn_x is None and cached_spawn and len(cached_spawn) >= 2:
            spawn_x = cached_spawn[0]
        if spawn_y is None and cached_spawn and len(cached_spawn) >= 2:
            spawn_y = cached_spawn[1]
    else:
        fail_stage = "resolve_base"
        t0 = time.ticks_ms()
        try:
            next_base = _resolve_asset_base(config["asset_bases"])
        except Exception as err:
            print("switch_map_skip_target:", target_map_id, err)
            print("switch_map_fail_stage:resolve_base")
            phase["resolve_base_ms"] = time.ticks_diff(time.ticks_ms(), t0)
            _print_switch_timings()
            _release_preload_cache("switch_fail")
            teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
            return False
        phase["resolve_base_ms"] = time.ticks_diff(time.ticks_ms(), t0)

    collision = None
    meta = None
    asset_base = None
    gc.collect()

    try:
        fail_stage = "map_context"
        load_phase = _load_map_context(
            next_base,
            fallback_all_walkable=fallback_all_walkable,
            prefer_stream=prefer_stream,
            preloaded_meta=next_meta,
            preloaded_collision=preloaded_collision,
        )
        phase["map_json_ms"] = load_phase["map_json_ms"]
        phase["tile_setup_ms"] = load_phase["tile_setup_ms"]
        phase["tile_load_ms"] = load_phase["tile_load_ms"]
        phase["collision_load_ms"] = load_phase["collision_load_ms"]
    except Exception as err:
        err_text = str(err)
        if ":" in err_text:
            fail_stage = err_text.split(":", 1)[0]
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
        print("switch_map_fail_stage:%s" % (fail_stage if fail_stage else "unknown"))
        _print_switch_timings()
        _release_preload_cache("switch_fail")
        teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
        gc.collect()
        return False

    fail_stage = "spawn_finalize"
    t0 = time.ticks_ms()
    used_meta_spawn = False
    if spawn_x is None:
        spawn_x = meta.get("spawn_x", world_w // 2)
        used_meta_spawn = True
    if spawn_y is None:
        spawn_y = meta.get("spawn_y", world_h // 2)
        used_meta_spawn = True
    if used_meta_spawn:
        spawn_x, spawn_y = _apply_spawn_offset_for_map(target_map_id, spawn_x, spawn_y)

    player_x = _clamp(spawn_x, PLAYER_R, world_w - PLAYER_R - 1)
    player_y = _clamp(spawn_y, PLAYER_R, world_h - PLAYER_R - 1)
    safe_x, safe_y = _nearest_walkable(player_x, player_y)
    if safe_x != player_x or safe_y != player_y:
        print("spawn_adjusted:", player_x, player_y, "->", safe_x, safe_y)
    player_x, player_y = safe_x, safe_y
    scroll_x = _clamp(player_x - ACTIVE_VIEW_W // 2, 0, world_w - ACTIVE_VIEW_W)
    scroll_y = _clamp(player_y - ACTIVE_VIEW_H // 2, 0, world_h - ACTIVE_VIEW_H)
    prev_scroll_x = scroll_x
    prev_scroll_y = scroll_y
    prev_player_x = player_x
    prev_player_y = player_y

    leaf_zone_prev_inside = False
    explore_overlay_dirty = False
    lamp_dialog_until_ms = 0
    # Keep startup-only intro effect; do not re-enable it on map switches.
    explore_force_full_redraw = True
    teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
    phase["spawn_finalize_ms"] = time.ticks_diff(time.ticks_ms(), t0)
    current_map_id = target_map_id
    _print_switch_timings()
    _release_preload_cache("switch_success")
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
    neutral = axis_max // DEADZONE_DIV
    # Midpoint guard: if startup calibration was biased, still allow reliable stop.
    mid_delta = raw - (axis_max // 2)
    if -neutral <= delta <= neutral or -neutral <= mid_delta <= neutral:
        return 0

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


def _expand_rect(rect, pad):
    x, y, w, h = rect
    return (x - pad, y - pad, w + (pad * 2), h + (pad * 2))


def _release_preload_cache(reason=None):
    global preload_cache
    if preload_cache is None:
        return
    if reason:
        print("preload_release:", reason)
    preload_cache = None
    gc.collect()


def _build_preload_cache(source_map_id, portal):
    global preload_cache

    started = time.ticks_ms()
    preload_cache = None

    target_map_id = portal.get("target_map_id")
    config = MAP_REGISTRY.get(target_map_id)
    if not config:
        print("preload_skip_missing_target:", target_map_id)
        print("preload_ms_total:", time.ticks_diff(time.ticks_ms(), started))
        return False

    try:
        next_base, next_meta = _find_asset_base(config["asset_bases"])
        map_w2 = next_meta["map_w"]
        map_h2 = next_meta["map_h"]
        collision_data, collision_err = _load_collision(next_meta, next_base, map_w2, map_h2)
        if collision_data is None:
            raise RuntimeError(collision_err if collision_err else "COLLISION_REQUIRED")

        preload_cache = {
            "source_map_id": source_map_id,
            "target_map_id": target_map_id,
            "base": next_base,
            "meta": next_meta,
            "collision": collision_data,
            "prefer_stream": bool(config.get("prefer_stream", False)),
            "spawn": portal.get("target_spawn"),
        }
        print("preload_ready:", source_map_id, "->", target_map_id, "base:", next_base)
        return True
    except Exception as err:
        print("preload_fail:", err)
        preload_cache = None
        return False
    finally:
        print("preload_ms_total:", time.ticks_diff(time.ticks_ms(), started))


def _get_current_portal(px, py):
    config = MAP_REGISTRY.get(current_map_id)
    if not config:
        return None
    portals = config.get("portals", ())
    for portal in portals:
        if _in_rect(px, py, portal["rect"]):
            return portal
    return None


def _update_preload_for_player(px, py):
    config = MAP_REGISTRY.get(current_map_id)
    if not config:
        _release_preload_cache("invalid_current_map")
        return

    portals = config.get("portals", ())
    preload_portal = None
    for portal in portals:
        if _in_rect(px, py, _expand_rect(portal["rect"], PRELOAD_PORTAL_PAD_PX)):
            preload_portal = portal
            break

    if preload_portal is None:
        _release_preload_cache("leave_preload_zone")
        return

    target_map_id = preload_portal.get("target_map_id")
    if (
        preload_cache is not None
        and preload_cache.get("source_map_id") == current_map_id
        and preload_cache.get("target_map_id") == target_map_id
    ):
        return

    _release_preload_cache("retarget_preload")
    _build_preload_cache(current_map_id, preload_portal)


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
battle_dialog_mode = BATTLE_DIALOG_NONE
battle_dialog_started_ms = 0
battle_dialog_png_info = None
battle_dialog_text = None
act_menu_active = False
act_choice_index = 0
act_sequence_step = 0
act_nav_prev_dir = 0
act_menu_slot_cache = None
act_prev_selected_index = -1
act_selection_dirty = False
item_menu_active = False
item_choice_index = 0
item_nav_prev_dir = 0
item_menu_slot_cache = None
item_prev_selected_index = -1
item_selection_dirty = False
item_view_offset = 0
menu_frame_x_used = battle_frame_x
menu_frame_w_used = BATTLE_FRAME_W
menu_cmd_y_used = battle_cmd_y
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
battle_menu_full_clear_pending = True
battle_menu_static_ready = False
battle_menu_static_frame_x = battle_frame_x
battle_menu_static_frame_y = battle_frame_y
battle_menu_static_frame_w = BATTLE_FRAME_W
battle_menu_enemy_bottom_used = battle_frame_y + 88
battle_menu_prev_dialog_active = False
battle_menu_prev_dialog_x = 0
battle_menu_prev_dialog_y = 0
battle_menu_prev_dialog_w = 0
battle_menu_prev_dialog_h = 0
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
inv_choice_index = 0
inv_nav_prev_dir = 0
inv_drop_active = False
inv_drop_choice_index = 0
inv_drop_nav_prev_dir = 0
inv_screen_dirty = True
INV_TAB_ITEM = 0
INV_TAB_STAT = 1
inv_tab_index = INV_TAB_ITEM
inv_tab_active = INV_TAB_ITEM
inv_tab_nav_prev_dir = 0
spawn_intro_cleared_once = False
spawn_intro_active = bool(ENABLE_SPAWN_INTRO and (current_map_id == MAP1_ID))
spawn_intro_overlay_path = _resolve_first_existing_path(SPAWN_OVERLAY_PATHS) if spawn_intro_active else None
spawn_intro_needs_redraw = spawn_intro_active
inventory_portrait_path = _resolve_first_existing_path(INVENTORY_PORTRAIT_PATHS)

if player_sheet_enabled:
    lgfx.player_frame_set(anim_row * 3 + anim_col)
    if hasattr(lgfx, "player_flip_x_set"):
        lgfx.player_flip_x_set(face_right)

_render_scene(scroll_x, scroll_y, player_x, player_y, True)
if spawn_intro_active:
    # Defer to draw_all() (function is defined later in file).
    # Calling it here before definition causes startup NameError -> reboot loop.
    spawn_intro_needs_redraw = True
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
    global lamp_dialog_until_ms, explore_force_full_redraw
    global spawn_intro_active, spawn_intro_cleared_once

    input_active = (x_dir != 0) or (y_dir_raw != 0)
    if spawn_intro_active and input_active:
        spawn_intro_active = False
        spawn_intro_cleared_once = True
        explore_force_full_redraw = True
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


def _draw_text_in_box(x, y, w, h, text, color=BATTLE_COLOR_WHITE):
    if not hasattr(lgfx, "draw_text"):
        return
    text_w = len(text) * 8
    tx = x + ((w - text_w) // 2)
    ty = y + ((h - 8) // 2)
    if tx < x + 2:
        tx = x + 2
    lgfx.draw_text(tx, ty, text, color)


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


def _menu_nav_dir_vertical():
    if y_dir_raw > 0:
        return 1
    if y_dir_raw < 0:
        return -1
    return 0


def _open_explore_inventory():
    global mode, inv_choice_index, inv_nav_prev_dir
    global inv_drop_active, inv_drop_choice_index, inv_drop_nav_prev_dir, inv_screen_dirty
    global inv_tab_index, inv_tab_active, inv_tab_nav_prev_dir

    mode = MODE_EXPLORE_INVENTORY
    inv_choice_index = inventory_clamp_index(inv_choice_index)
    inv_nav_prev_dir = 0
    inv_drop_active = False
    inv_drop_choice_index = 0
    inv_drop_nav_prev_dir = 0
    inv_tab_index = INV_TAB_ITEM
    inv_tab_active = INV_TAB_ITEM
    inv_tab_nav_prev_dir = 0
    inv_screen_dirty = True


def _close_explore_inventory():
    global mode, explore_force_full_redraw
    global inv_nav_prev_dir, inv_drop_active, inv_drop_choice_index, inv_drop_nav_prev_dir, inv_screen_dirty
    global inv_tab_nav_prev_dir

    mode = MODE_EXPLORE
    explore_force_full_redraw = True
    inv_nav_prev_dir = 0
    inv_drop_active = False
    inv_drop_choice_index = 0
    inv_drop_nav_prev_dir = 0
    inv_tab_nav_prev_dir = 0
    inv_screen_dirty = True


def _draw_explore_inventory_screen():
    panel_border = BATTLE_CMD_BORDER_THICK
    frame_border = BATTLE_FRAME_BORDER_THICK
    left_w = 112
    pad = 8
    box_x = 4
    box_y = 4
    box_w = ACTIVE_VIEW_W - 8
    box_h = ACTIVE_VIEW_H - 8
    if box_w < 40 or box_h < 40:
        return

    lgfx.clear()
    _draw_rect_thick(box_x, box_y, box_w, box_h, BATTLE_COLOR_WHITE, frame_border)

    left_x = box_x + pad
    left_y = box_y + pad
    right_h = box_h - (pad * 2)
    status_bottom = left_y + 72 + 8 + 6  # HP text baseline + font height + small margin
    left_h = status_bottom - left_y
    if left_h > right_h:
        left_h = right_h
    if left_h < 40:
        left_h = 40
    right_x = left_x + left_w + 8
    right_y = left_y
    right_w = box_x + box_w - pad - right_x

    _draw_rect_thick(left_x, left_y, left_w, left_h, BATTLE_COLOR_WHITE, panel_border)
    _draw_rect_thick(right_x, right_y, right_w, right_h, BATTLE_COLOR_WHITE, panel_border)

    if hasattr(lgfx, "draw_text"):
        lgfx.draw_text(left_x + 8, left_y + 10, "NAME", BATTLE_COLOR_WHITE)
        lgfx.draw_text(left_x + 8, left_y + 24, PLAYER_NAME, BATTLE_COLOR_WHITE)
        lgfx.draw_text(left_x + 8, left_y + 52, "LV %d" % PLAYER_LV, BATTLE_COLOR_WHITE)
        lgfx.draw_text(left_x + 8, left_y + 72, "HP %d/%d" % (player_hp, PLAYER_HP_MAX), BATTLE_COLOR_WHITE)

    tab_x = left_x + 8
    tab_y = left_y + left_h + 4
    tab_w = left_w - 16
    tab_row_h = 14
    tabs = ("ITEM", "STAT")
    for i, label in enumerate(tabs):
        ry = tab_y + i * tab_row_h
        if i == inv_tab_index:
            line_h = panel_border
            if line_h > tab_row_h:
                line_h = tab_row_h
            lgfx.draw_rect(tab_x, ry + tab_row_h - line_h, tab_w, line_h, BATTLE_COLOR_RED)
        text_color = BATTLE_CMD_COLOR if i == inv_tab_active else BATTLE_COLOR_WHITE
        _draw_text_in_box(tab_x + 2, ry, tab_w - 4, tab_row_h, label, text_color)

    title_h = 16
    right_title = "ITEM" if inv_tab_active == INV_TAB_ITEM else "STAT"
    _draw_text_in_box(right_x + 2, right_y + 2, right_w - 4, title_h, right_title, BATTLE_CMD_COLOR)
    list_x = right_x + 4
    list_y = right_y + title_h + 4
    list_w = right_w - 8
    list_h = right_h - title_h - 8

    if inv_tab_active == INV_TAB_ITEM:
        if inventory_is_empty():
            _draw_text_in_box(list_x, list_y, list_w, list_h, "EMPTY", BATTLE_COLOR_WHITE)
        else:
            rows = INVENTORY_CAPACITY
            row_h = list_h // rows
            if row_h < 12:
                row_h = 12
                rows = list_h // row_h
                if rows < 1:
                    rows = 1
            for i in range(rows):
                ry = list_y + i * row_h
                if ry + row_h > list_y + list_h:
                    break
                if i >= len(inventory_items):
                    break
                row_item = inventory_items[i]
                if i == inv_choice_index and not inv_drop_active:
                    line_h = panel_border
                    if line_h > row_h:
                        line_h = row_h
                    lgfx.draw_rect(list_x, ry + row_h - line_h, list_w, line_h, BATTLE_COLOR_RED)
                _draw_text_in_box(list_x + 2, ry, list_w - 4, row_h, row_item.get("name", "Item"), BATTLE_COLOR_WHITE)
    else:
        top_h = 14
        row_h = 16
        top_y = list_y + 2
        _draw_text_in_box(list_x + 2, top_y, list_w - 4, top_h, PLAYER_NAME, BATTLE_COLOR_WHITE)
        _draw_text_in_box(list_x + 2, top_y + row_h, list_w - 4, top_h, "LV %d" % PLAYER_LV, BATTLE_COLOR_WHITE)
        _draw_text_in_box(list_x + 2, top_y + (row_h * 2), list_w - 4, top_h, "HP %d/%d" % (player_hp, PLAYER_HP_MAX), BATTLE_COLOR_WHITE)

        info_y = top_y + (row_h * 3) + 6
        at_text = "AT %d(%d)" % (PLAYER_AT_BASE, PLAYER_AT_BONUS)
        df_text = "DF %d(%d)" % (PLAYER_DF_BASE, PLAYER_DF_BONUS)
        _draw_text_in_box(list_x + 2, info_y, list_w - 4, top_h, at_text, BATTLE_COLOR_WHITE)
        _draw_text_in_box(list_x + 2, info_y + row_h, list_w - 4, top_h, df_text, BATTLE_COLOR_WHITE)
        _draw_text_in_box(list_x + 2, info_y + (row_h * 2), list_w - 4, top_h, "WEAPON: %s" % PLAYER_WEAPON, BATTLE_COLOR_WHITE)
        _draw_text_in_box(list_x + 2, info_y + (row_h * 3), list_w - 4, top_h, "ARMOR: %s" % PLAYER_ARMOR, BATTLE_COLOR_WHITE)

    if inv_tab_active != INV_TAB_ITEM or not inv_drop_active:
        return

    menu_w = 84
    menu_h = 52
    menu_x = right_x + (right_w - menu_w) // 2
    menu_y = right_y + (right_h - menu_h) // 2
    _fill_rect_solid(menu_x, menu_y, menu_w, menu_h, 0x0000)
    _draw_rect_thick(menu_x, menu_y, menu_w, menu_h, BATTLE_COLOR_WHITE, panel_border)
    keep_color = BATTLE_COLOR_RED if inv_drop_choice_index == 0 else BATTLE_COLOR_WHITE
    drop_color = BATTLE_COLOR_RED if inv_drop_choice_index == 1 else BATTLE_COLOR_WHITE
    _draw_text_in_box(menu_x + 4, menu_y + 8, menu_w - 8, 16, "KEEP", keep_color)
    _draw_text_in_box(menu_x + 4, menu_y + 28, menu_w - 8, 16, "DROP", drop_color)


def update_explore_inventory(loop_start, item_pressed, interact_pressed):
    del loop_start
    global inv_choice_index, inv_nav_prev_dir
    global inv_drop_active, inv_drop_choice_index, inv_drop_nav_prev_dir
    global inv_screen_dirty
    global inv_tab_index, inv_tab_active, inv_tab_nav_prev_dir

    if item_pressed:
        _close_explore_inventory()
        return

    if inv_drop_active:
        nav_dir = _menu_nav_dir_vertical()
        if nav_dir != 0 and nav_dir != inv_drop_nav_prev_dir:
            # KEEP/DROP uses two choices; always toggle on a valid up/down edge
            # so pressing up from KEEP can move to DROP (and vice versa).
            inv_drop_choice_index = (inv_drop_choice_index + 1) % 2
            inv_screen_dirty = True
        inv_drop_nav_prev_dir = nav_dir
        if not interact_pressed:
            return
        if inv_drop_choice_index == 1:
            inventory_remove_at(inv_choice_index)
            inv_choice_index = inventory_clamp_index(inv_choice_index)
        inv_drop_active = False
        inv_drop_choice_index = 0
        inv_drop_nav_prev_dir = 0
        inv_screen_dirty = True
        return

    nav_dir = _menu_nav_dir_vertical()
    if nav_dir != 0 and nav_dir != inv_tab_nav_prev_dir:
        inv_tab_index = (inv_tab_index + 1) % 2
        inv_screen_dirty = True
    inv_tab_nav_prev_dir = nav_dir

    if inventory_is_empty():
        inv_choice_index = 0

    if interact_pressed:
        if inv_tab_active != inv_tab_index:
            inv_tab_active = inv_tab_index
            inv_drop_active = False
            inv_drop_choice_index = 0
            inv_drop_nav_prev_dir = 0
            inv_nav_prev_dir = 0
            inv_screen_dirty = True
            return
        if inv_tab_active == INV_TAB_STAT:
            return
        if not inventory_is_empty():
            inv_drop_active = True
            inv_drop_choice_index = 0
            inv_drop_nav_prev_dir = 0
            inv_screen_dirty = True
        return

    inv_nav_prev_dir = 0


def _draw_spawn_intro_overlay():
    cx = player_x - scroll_x
    cy = player_y - scroll_y
    view_w = ACTIVE_VIEW_W
    view_h = ACTIVE_VIEW_H
    r = SPAWN_SPOTLIGHT_RADIUS
    if r < 1:
        r = 1
    rr = r * r

    top = cy - r
    bottom = cy + r
    if top > 0:
        _fill_rect_solid(0, 0, view_w, top, 0x0000)
    if bottom < (view_h - 1):
        y2 = bottom + 1
        _fill_rect_solid(0, y2, view_w, view_h - y2, 0x0000)

    yy = top if top > 0 else 0
    y_end = bottom if bottom < (view_h - 1) else (view_h - 1)
    while yy <= y_end:
        dy = yy - cy
        if dy < 0:
            dy = -dy

        dx = _isqrt(rr - (dy * dy))
        left = cx - dx
        right = cx + dx

        if left > 0:
            lgfx.draw_rect(0, yy, left, 1, 0x0000)
        if right < (view_w - 1):
            x2 = right + 1
            lgfx.draw_rect(x2, yy, view_w - x2, 1, 0x0000)
        yy += 1

    if spawn_intro_overlay_path and hasattr(lgfx, "draw_png_file"):
        lgfx.draw_png_file(
            spawn_intro_overlay_path,
            cx - (PLAYER_FRAME_W // 2),
            cy - (PLAYER_FRAME_H // 2),
            PLAYER_FRAME_W,
            PLAYER_FRAME_H,
        )


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


def _draw_battle_frame(frame_x=None, frame_y=None, frame_w=None, frame_h=None):
    if frame_x is None:
        frame_x = battle_frame_x
    if frame_y is None:
        frame_y = battle_frame_y
    if frame_w is None:
        frame_w = BATTLE_FRAME_W
    if frame_h is None:
        frame_h = BATTLE_FRAME_H
    _draw_rect_thick(
        frame_x,
        frame_y,
        frame_w,
        frame_h,
        BATTLE_COLOR_WHITE,
        BATTLE_FRAME_BORDER_THICK,
    )


def _battle_menu_geometry(frame_w):
    frame_h = BATTLE_FRAME_H
    frame_x = (ACTIVE_VIEW_W - frame_w) // 2
    frame_y = (ACTIVE_VIEW_H - frame_h) // 2
    if frame_x < 0:
        frame_x = 0
    if frame_y < 0:
        frame_y = 0
    cmd_w = (frame_w - (BATTLE_CMD_MARGIN_X * 2) - (BATTLE_CMD_GAP * 3)) // 4
    if cmd_w < 16:
        cmd_w = 16
    cmd_x0 = frame_x + BATTLE_CMD_MARGIN_X
    cmd_y = frame_y + frame_h - BATTLE_CMD_H - 10
    return frame_x, frame_y, cmd_x0, cmd_y, cmd_w


def _clear_rect_black(x, y, w, h):
    if w <= 0 or h <= 0:
        return
    if x < 0:
        w += x
        x = 0
    if y < 0:
        h += y
        y = 0
    if w <= 0 or h <= 0:
        return
    max_w = ACTIVE_VIEW_W - x
    max_h = ACTIVE_VIEW_H - y
    if max_w <= 0 or max_h <= 0:
        return
    if w > max_w:
        w = max_w
    if h > max_h:
        h = max_h
    _fill_rect_solid(x, y, w, h, 0x0000)


def _rect_union(x1, y1, w1, h1, x2, y2, w2, h2):
    if w1 <= 0 or h1 <= 0:
        return x2, y2, w2, h2
    if w2 <= 0 or h2 <= 0:
        return x1, y1, w1, h1
    x = x1 if x1 < x2 else x2
    y = y1 if y1 < y2 else y2
    x2_max = x2 + w2
    x1_max = x1 + w1
    y2_max = y2 + h2
    y1_max = y1 + h1
    right = x1_max if x1_max > x2_max else x2_max
    bottom = y1_max if y1_max > y2_max else y2_max
    return x, y, right - x, bottom - y


def _draw_battle_menu_static_layer(frame_x, frame_y, frame_w, cmd_x0, cmd_y, cmd_w):
    _draw_battle_frame(frame_x, frame_y, frame_w, BATTLE_FRAME_H)

    enemy_x = frame_x + ((frame_w - ENEMY_SPRITE_W) // 2)
    enemy_y = frame_y + 16
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
        monster_cx = frame_x + (frame_w // 2)
        monster_cy = frame_y + 75
        lgfx.draw_circle(monster_cx, monster_cy, 22, BATTLE_COLOR_WHITE)
        enemy_bottom = monster_cy + 22

    for i, label in enumerate(("FIGHT", "ACT", "ITEM", "MERCY")):
        bx = cmd_x0 + i * (cmd_w + BATTLE_CMD_GAP)
        by = cmd_y
        _draw_rect_thick(bx, by, cmd_w, BATTLE_CMD_H, BATTLE_CMD_COLOR, BATTLE_CMD_BORDER_THICK)
        content_x = bx + 1
        content_y = by + 1
        content_w = cmd_w - 2
        content_h = BATTLE_CMD_H - 2
        icon_w = 8
        icon_gap = 2
        icon_shift = 2 if (i == 1 or i == 2) else 1
        icon_x = content_x + icon_shift
        text_x = icon_x + icon_w + icon_gap
        text_w = content_w - (icon_x - content_x) - icon_w - icon_gap
        if text_w > 0 and _draw_cmd_icon_with_fallback(i, icon_x, content_y, icon_w, content_h):
            _draw_text_in_box(text_x, content_y, text_w, content_h, label, BATTLE_CMD_COLOR)
        else:
            _draw_text_in_box(bx, by, cmd_w, BATTLE_CMD_H, label, BATTLE_CMD_COLOR)

    return enemy_bottom


def _draw_png_in_box(png_info, x, y, w, h, preserve_aspect=True, allow_upscale=False):
    if not hasattr(lgfx, "draw_png_file"):
        return False
    if not png_info:
        return False
    path, src_w, src_h = png_info
    if not _path_exists(path):
        return False
    if w < 1 or h < 1:
        return False
    draw_w = w
    draw_h = h
    if preserve_aspect and src_w > 0 and src_h > 0:
        scale_w = (w << 8) // src_w
        scale_h = (h << 8) // src_h
        scale = scale_w if scale_w < scale_h else scale_h
        if not allow_upscale and scale > 256:
            scale = 256
        if scale < 1:
            scale = 1
        draw_w = (src_w * scale) >> 8
        draw_h = (src_h * scale) >> 8
        if draw_w < 1:
            draw_w = 1
        if draw_h < 1:
            draw_h = 1
    draw_x = x + ((w - draw_w) // 2)
    draw_y = y + ((h - draw_h) // 2)
    try:
        return bool(lgfx.draw_png_file(path, draw_x, draw_y, draw_w, draw_h))
    except Exception:
        return False


def _draw_cmd_icon_with_fallback(icon_index, x, y, w, h):
    if icon_index < 0 or icon_index >= len(CMD_ICON_PATHS):
        return False
    for path in CMD_ICON_PATHS[icon_index]:
        if not _path_exists(path):
            continue
        if _draw_png_in_box(
            (path, CMD_ICON_SRC_W, CMD_ICON_SRC_H),
            x,
            y,
            w,
            h,
            preserve_aspect=True,
            allow_upscale=False,
        ):
            return True
    return False


def _draw_star_line_with_png(png_info, x, y, w, h):
    if w < 8 or h < 8:
        return False
    icon_pad = 2
    star_size = h - (icon_pad * 2)
    if star_size > 22:
        star_size = 22
    if star_size < 10:
        star_size = 10
    star_drawn = False
    for path in STAR_ICON_PATHS:
        if not _path_exists(path):
            continue
        star_drawn = _draw_png_in_box(
            (path, STAR_ICON_SRC_W, STAR_ICON_SRC_H),
            x + icon_pad,
            y + icon_pad,
            star_size,
            star_size,
            preserve_aspect=True,
            allow_upscale=False,
        )
        if star_drawn:
            break
    if not star_drawn and hasattr(lgfx, "draw_text"):
        _draw_text_in_box(
            x + icon_pad,
            y + icon_pad,
            star_size,
            star_size,
            "*",
            BATTLE_COLOR_RED,
        )
        star_drawn = True
    text_x = x + icon_pad + star_size + 2
    text_w = w - (text_x - x) - icon_pad
    if text_w < 1:
        return star_drawn
    return _draw_png_in_box(
        png_info,
        text_x,
        y + 1,
        text_w,
        h - 2,
        preserve_aspect=True,
        allow_upscale=False,
    ) or star_drawn


def _draw_star_line_with_text(text, x, y, w, h):
    if w < 8 or h < 8:
        return False
    icon_pad = 2
    star_size = h - (icon_pad * 2)
    if star_size > 24:
        star_size = 24
    if star_size < 18:
        star_size = 18
    star_drawn = False
    for path in STAR_ICON_PATHS:
        if not _path_exists(path):
            continue
        star_drawn = _draw_png_in_box(
            (path, STAR_ICON_SRC_W, STAR_ICON_SRC_H),
            x + icon_pad,
            y + icon_pad,
            star_size,
            star_size,
            preserve_aspect=True,
            allow_upscale=False,
        )
        if star_drawn:
            break
    if not star_drawn and hasattr(lgfx, "draw_text"):
        _draw_text_in_box(
            x + icon_pad,
            y + icon_pad,
            star_size,
            star_size,
            "*",
            BATTLE_COLOR_RED,
        )
        star_drawn = True
    text_x = x + icon_pad + star_size + 2
    text_w = w - (text_x - x) - icon_pad
    if text_w < 1:
        return star_drawn
    if not hasattr(lgfx, "draw_text"):
        return star_drawn
    max_chars = text_w // 8
    if max_chars < 1:
        return star_drawn
    clipped = text
    if len(clipped) > max_chars:
        clipped = clipped[:max_chars]
    ty = y + ((h - 8) // 2)
    lgfx.draw_text(text_x, ty, clipped, BATTLE_COLOR_WHITE)
    return True


def _draw_act_selection_indicator(prev_index, next_index, slots):
    if not slots:
        return
    if prev_index >= 0 and prev_index < len(slots):
        px, py, pw, ph = slots[prev_index]
        lgfx.draw_rect(px, py + ph - 1, pw, 1, 0x0000)
    if next_index >= 0 and next_index < len(slots):
        nx, ny, nw, nh = slots[next_index]
        lgfx.draw_rect(nx, ny + nh - 1, nw, 1, BATTLE_COLOR_RED)


def _resolve_item_dialog_layout():
    frame_w = BATTLE_FRAME_W
    max_frame_w = ACTIVE_VIEW_W - 4
    if max_frame_w < frame_w:
        max_frame_w = frame_w
    while True:
        frame_x, frame_y, cmd_x0, cmd_y, cmd_w = _battle_menu_geometry(frame_w)
        dialog_x = frame_x + 10
        dialog_w = frame_w - 20
        enemy_bottom_est = frame_y + 97
        dialog_y = enemy_bottom_est + 6
        dialog_h = cmd_y - dialog_y - 6
        if dialog_h < 20:
            dialog_h = 20
            dialog_y = cmd_y - dialog_h - 6
        min_dialog_y = frame_y + 8
        if dialog_y < min_dialog_y:
            dialog_y = min_dialog_y
            dialog_h = cmd_y - dialog_y - 6
        if dialog_h < 20:
            dialog_h = 20

        inner_x = dialog_x + 4
        inner_y = dialog_y + 4
        inner_w = dialog_w - 8
        inner_h = dialog_h - 8
        if inner_w < 12 or inner_h < 12:
            slots = None
        else:
            slot_rows = 2
            gap = 3
            slot_h = (inner_h - (gap * (slot_rows - 1))) // slot_rows
            if slot_h < 10:
                slot_h = -1
            if slot_h > 0:
                slots = []
                y = inner_y
                for _ in range(slot_rows):
                    slots.append((inner_x, y, inner_w, slot_h))
                    y += slot_h + gap
            else:
                slots = None

        if slots:
            return frame_w, frame_x, frame_y, cmd_x0, cmd_y, cmd_w, dialog_x, dialog_y, dialog_w, dialog_h, slots
        if frame_w >= max_frame_w:
            return frame_w, frame_x, frame_y, cmd_x0, cmd_y, cmd_w, dialog_x, dialog_y, dialog_w, dialog_h, None
        frame_w += 24
        if frame_w > max_frame_w:
            frame_w = max_frame_w


def _reset_item_menu_state():
    global item_menu_active, item_choice_index, item_nav_prev_dir
    global item_menu_slot_cache, item_prev_selected_index
    global item_selection_dirty, item_view_offset

    item_menu_active = False
    item_choice_index = 0
    item_nav_prev_dir = 0
    item_menu_slot_cache = None
    item_prev_selected_index = -1
    item_selection_dirty = False
    item_view_offset = 0


def _use_battle_item_at(index):
    global player_hp, battle_status_dirty

    item = inventory_remove_at(index)
    if not item:
        return "No items"

    name = item.get("name", "Item")
    heal_amount = int(item.get("heal_amount", 0))
    if heal_amount > 0:
        before = player_hp
        player_hp += heal_amount
        if player_hp > PLAYER_HP_MAX:
            player_hp = PLAYER_HP_MAX
        gain = player_hp - before
        if gain < 0:
            gain = 0
        battle_status_dirty = True
        return "Used %s  HP +%d" % (name, gain)
    return "Used %s" % name


def _act_slots_for_layout(mode, inner_x, inner_y, inner_w, inner_h):
    gap = 4
    if inner_w < 12 or inner_h < 12:
        return None
    if mode == 1:
        slot_w = (inner_w - gap) // 2
        slot_h = (inner_h - gap) // 2
        if slot_w < 8 or slot_h < 8:
            return None
        slot0 = (inner_x, inner_y, slot_w, slot_h)
        slot1 = (inner_x, inner_y + slot_h + gap, slot_w, slot_h)
        slot2 = (inner_x + slot_w + gap, inner_y, slot_w, slot_h)
        return (slot0, slot1, slot2)
    slot_h = (inner_h - (gap * 2)) // 3
    if slot_h < 8:
        return None
    slot0 = (inner_x, inner_y, inner_w, slot_h)
    slot1 = (inner_x, inner_y + slot_h + gap, inner_w, slot_h)
    slot2 = (inner_x, inner_y + (slot_h * 2) + (gap * 2), inner_w, slot_h)
    return (slot0, slot1, slot2)


def _act_slots_fit(slots):
    min_scale_q8 = 220  # ~0.86, keep text close to native size for clarity
    for i, slot in enumerate(slots):
        _, src_w, src_h = ACT_OPTION_PNG_INFOS[i]
        slot_h = slot[3]
        star_size = slot_h - 4
        if star_size > 22:
            star_size = 22
        if star_size < 10:
            star_size = 10
        # Match _draw_star_line_with_png() layout: icon_pad(2) + star + gap(2) + right pad(2)
        text_w = slot[2] - (2 + star_size + 2 + 2)
        text_h = slot_h - 2
        if text_w < 1 or text_h < 1:
            return False
        scale_w = (text_w << 8) // src_w
        scale_h = (text_h << 8) // src_h
        scale = scale_w if scale_w < scale_h else scale_h
        if scale < min_scale_q8:
            return False
    return True


def _resolve_act_dialog_layout():
    frame_w = BATTLE_FRAME_W
    max_frame_w = ACTIVE_VIEW_W - 4
    if max_frame_w < frame_w:
        max_frame_w = frame_w
    while True:
        frame_x, frame_y, cmd_x0, cmd_y, cmd_w = _battle_menu_geometry(frame_w)
        dialog_x = frame_x + 10
        dialog_w = frame_w - 20
        enemy_bottom_est = frame_y + 97
        dialog_y = enemy_bottom_est + 6
        dialog_h = cmd_y - dialog_y - 6
        if dialog_h < 20:
            dialog_h = 20
            dialog_y = cmd_y - dialog_h - 6
        min_dialog_y = frame_y + 8
        if dialog_y < min_dialog_y:
            dialog_y = min_dialog_y
            dialog_h = cmd_y - dialog_y - 6
        if dialog_h < 20:
            dialog_h = 20
        inner_x = dialog_x + 4
        inner_y = dialog_y + 4
        inner_w = dialog_w - 8
        inner_h = dialog_h - 8
        slots_lr = _act_slots_for_layout(1, inner_x, inner_y, inner_w, inner_h)
        if slots_lr and _act_slots_fit(slots_lr):
            return frame_w, frame_x, frame_y, cmd_x0, cmd_y, cmd_w, dialog_x, dialog_y, dialog_w, dialog_h, slots_lr
        slots_col = _act_slots_for_layout(2, inner_x, inner_y, inner_w, inner_h)
        if slots_col and _act_slots_fit(slots_col):
            return frame_w, frame_x, frame_y, cmd_x0, cmd_y, cmd_w, dialog_x, dialog_y, dialog_w, dialog_h, slots_col
        if frame_w >= max_frame_w:
            fallback_slots = slots_col
            if fallback_slots is None:
                fallback_slots = _act_slots_for_layout(2, inner_x, inner_y, inner_w, inner_h)
            return frame_w, frame_x, frame_y, cmd_x0, cmd_y, cmd_w, dialog_x, dialog_y, dialog_w, dialog_h, fallback_slots
        frame_w += 24
        if frame_w > max_frame_w:
            frame_w = max_frame_w


def _draw_battle_menu_screen(dialog_active):
    global menu_frame_x_used, menu_frame_w_used, menu_cmd_y_used
    global act_menu_slot_cache, act_prev_selected_index
    global item_menu_slot_cache, item_prev_selected_index, item_view_offset
    global battle_menu_full_clear_pending
    global battle_menu_static_ready, battle_menu_static_frame_x, battle_menu_static_frame_y, battle_menu_static_frame_w
    global battle_menu_enemy_bottom_used
    global battle_menu_prev_dialog_active, battle_menu_prev_dialog_x, battle_menu_prev_dialog_y
    global battle_menu_prev_dialog_w, battle_menu_prev_dialog_h

    if act_menu_active:
        (
            frame_w,
            frame_x,
            frame_y,
            cmd_x0,
            cmd_y,
            cmd_w,
            dialog_x,
            dialog_y,
            dialog_w,
            dialog_h,
            act_slots,
        ) = _resolve_act_dialog_layout()
        item_slots = None
    elif item_menu_active:
        (
            frame_w,
            frame_x,
            frame_y,
            cmd_x0,
            cmd_y,
            cmd_w,
            dialog_x,
            dialog_y,
            dialog_w,
            dialog_h,
            item_slots,
        ) = _resolve_item_dialog_layout()
        act_slots = None
    else:
        frame_w = BATTLE_FRAME_W
        frame_x, frame_y, cmd_x0, cmd_y, cmd_w = _battle_menu_geometry(frame_w)
        dialog_x = frame_x + 10
        dialog_w = frame_w - 20
        dialog_h = 28
        dialog_y = frame_y + 94
        act_slots = None
        item_slots = None

    menu_frame_x_used = frame_x
    menu_frame_w_used = frame_w
    menu_cmd_y_used = cmd_y

    did_full_clear = False
    if battle_menu_full_clear_pending:
        lgfx.clear()
        battle_menu_full_clear_pending = False
        battle_menu_static_ready = False
        battle_menu_prev_dialog_active = False
        did_full_clear = True

    static_changed = (
        (not battle_menu_static_ready)
        or (frame_x != battle_menu_static_frame_x)
        or (frame_y != battle_menu_static_frame_y)
        or (frame_w != battle_menu_static_frame_w)
    )
    if static_changed:
        if (not did_full_clear) and battle_menu_static_ready:
            clear_x, clear_y, clear_w, clear_h = _rect_union(
                battle_menu_static_frame_x,
                battle_menu_static_frame_y,
                battle_menu_static_frame_w,
                BATTLE_FRAME_H,
                frame_x,
                frame_y,
                frame_w,
                BATTLE_FRAME_H,
            )
            _clear_rect_black(clear_x, clear_y, clear_w, clear_h)
            battle_menu_prev_dialog_active = False
        battle_menu_enemy_bottom_used = _draw_battle_menu_static_layer(frame_x, frame_y, frame_w, cmd_x0, cmd_y, cmd_w)
        battle_menu_static_frame_x = frame_x
        battle_menu_static_frame_y = frame_y
        battle_menu_static_frame_w = frame_w
        battle_menu_static_ready = True

    if not dialog_active:
        act_menu_slot_cache = None
        act_prev_selected_index = -1
        item_menu_slot_cache = None
        item_prev_selected_index = -1
        if battle_menu_prev_dialog_active:
            _clear_rect_black(
                battle_menu_prev_dialog_x,
                battle_menu_prev_dialog_y,
                battle_menu_prev_dialog_w,
                battle_menu_prev_dialog_h,
            )
            battle_menu_prev_dialog_active = False
        return

    dialog_render_y = dialog_y
    if not act_menu_active and not item_menu_active:
        dialog_render_y = battle_menu_enemy_bottom_used + 6
        max_dialog_y = cmd_y - dialog_h - 6
        if dialog_render_y > max_dialog_y:
            dialog_render_y = max_dialog_y

    clear_x = dialog_x
    clear_y = dialog_render_y
    clear_w = dialog_w
    clear_h = dialog_h
    if battle_menu_prev_dialog_active:
        clear_x, clear_y, clear_w, clear_h = _rect_union(
            clear_x,
            clear_y,
            clear_w,
            clear_h,
            battle_menu_prev_dialog_x,
            battle_menu_prev_dialog_y,
            battle_menu_prev_dialog_w,
            battle_menu_prev_dialog_h,
        )
    _clear_rect_black(clear_x, clear_y, clear_w, clear_h)
    battle_menu_prev_dialog_active = True
    battle_menu_prev_dialog_x = dialog_x
    battle_menu_prev_dialog_y = dialog_render_y
    battle_menu_prev_dialog_w = dialog_w
    battle_menu_prev_dialog_h = dialog_h

    if act_menu_active and act_slots:
        act_menu_slot_cache = act_slots
        act_prev_selected_index = act_choice_index
        for i, slot in enumerate(act_slots):
            if i == act_choice_index:
                lgfx.draw_rect(slot[0], slot[1] + slot[3] - 1, slot[2], 1, BATTLE_COLOR_RED)
            _draw_star_line_with_png(
                ACT_OPTION_PNG_INFOS[i],
                slot[0],
                slot[1],
                slot[2],
                slot[3],
            )
        return

    if item_menu_active and item_slots:
        item_menu_slot_cache = item_slots
        item_prev_selected_index = item_choice_index
        total = len(inventory_items)
        if total <= 0:
            _draw_text_in_box(dialog_x, dialog_render_y, dialog_w, dialog_h, "No items", BATTLE_COLOR_WHITE)
            return
        rows = len(item_slots)
        if rows < 1:
            rows = 1
        item_choice = inventory_clamp_index(item_choice_index)
        if item_choice < item_view_offset:
            item_view_offset = item_choice
        if item_choice >= item_view_offset + rows:
            item_view_offset = item_choice - rows + 1
        max_start = total - rows
        if max_start < 0:
            max_start = 0
        if item_view_offset > max_start:
            item_view_offset = max_start
        if item_view_offset < 0:
            item_view_offset = 0

        for i, slot in enumerate(item_slots):
            item_i = item_view_offset + i
            if item_i >= total:
                continue
            if item_i == item_choice:
                lgfx.draw_rect(slot[0], slot[1] + slot[3] - 1, slot[2], 1, BATTLE_COLOR_RED)
            _draw_star_line_with_text(
                inventory_items[item_i].get("name", "Item"),
                slot[0],
                slot[1],
                slot[2],
                slot[3],
            )
        return

    act_menu_slot_cache = None
    act_prev_selected_index = -1
    item_menu_slot_cache = None
    item_prev_selected_index = -1

    # Reply mode: fixed single-line centered render with no text fallback.
    if battle_dialog_png_info:
        _draw_star_line_with_png(
            battle_dialog_png_info,
            dialog_x,
            dialog_render_y + ((dialog_h - 20) // 2),
            dialog_w,
            20,
        )
    elif battle_dialog_text:
        _draw_text_in_box(
            dialog_x + 4,
            dialog_render_y + ((dialog_h - 16) // 2),
            dialog_w - 8,
            16,
            battle_dialog_text,
            BATTLE_COLOR_WHITE,
        )


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
    global bullets, next_bullet_spawn_ms, damage_invuln_until_ms
    global battle_bullets_dirty, battle_prev_bullet_positions, battle_status_dirty
    global fight_heart_x, fight_heart_y, battle_prev_heart_x, battle_prev_heart_y

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


def _clear_act_dialog_state(reset_sequence):
    global act_menu_active, act_choice_index, act_nav_prev_dir, act_sequence_step
    global battle_dialog_mode, battle_dialog_started_ms, battle_dialog_png_info, battle_dialog_text
    global act_dialog_until_ms
    global act_menu_slot_cache, act_prev_selected_index, act_selection_dirty

    act_menu_active = False
    act_choice_index = 0
    act_nav_prev_dir = 0
    act_menu_slot_cache = None
    act_prev_selected_index = -1
    act_selection_dirty = False
    battle_dialog_mode = BATTLE_DIALOG_NONE
    battle_dialog_started_ms = 0
    battle_dialog_png_info = None
    battle_dialog_text = None
    act_dialog_until_ms = 0
    _reset_item_menu_state()
    if reset_sequence:
        act_sequence_step = 0


def _start_battle_from_explore():
    global mode, mercy_exit_pending
    global battle_menu_dirty, battle_dialog_visible
    global battle_menu_full_clear_pending
    global battle_menu_static_ready, battle_menu_prev_dialog_active
    global explore_moved, explore_scrolled, explore_anim_changed
    global lamp_dialog_until_ms, explore_overlay_dirty

    mode = MODE_BATTLE_MENU
    _clear_act_dialog_state(True)
    mercy_exit_pending = False
    battle_menu_dirty = True
    battle_dialog_visible = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    battle_menu_prev_dialog_active = False
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
    name_text = MONSTER_NAME
    hp_text = "HP"
    right_text = "%2d/%d" % (player_hp, PLAYER_HP_MAX)
    x = battle_frame_x + 12
    if in_menu:
        x = menu_frame_x_used + 12
        y = menu_cmd_y_used - (8 + BATTLE_STATUS_TO_CMD_GAP)
    else:
        y = _battle_status_y()

    def _draw_bold_text(tx, ty, text):
        # Simulate a slightly larger/bolder look using 2x2 overdraw.
        lgfx.draw_text(tx, ty, text, BATTLE_COLOR_WHITE)
        lgfx.draw_text(tx + 1, ty, text, BATTLE_COLOR_WHITE)
        lgfx.draw_text(tx, ty + 1, text, BATTLE_COLOR_WHITE)
        lgfx.draw_text(tx + 1, ty + 1, text, BATTLE_COLOR_WHITE)

    _draw_bold_text(x, y, name_text)
    name_w = len(name_text) * 8
    hp_x = x + name_w + BATTLE_HP_NAME_TO_HP_GAP
    _draw_bold_text(hp_x, y, hp_text)

    hp_w = len(hp_text) * 8
    bar_x = hp_x + hp_w + BATTLE_HP_BAR_GAP
    bar_y = y + ((8 - BATTLE_HP_BAR_H) // 2)
    if bar_y < y:
        bar_y = y
    bar_w = BATTLE_HP_BAR_W
    bar_h = BATTLE_HP_BAR_H

    _draw_rect_thick(bar_x, bar_y, bar_w, bar_h, BATTLE_COLOR_WHITE, 1)
    inner_x = bar_x + 1
    inner_y = bar_y + 1
    inner_w = bar_w - 2
    inner_h = bar_h - 2
    if inner_w > 0 and inner_h > 0:
        _fill_rect_solid(inner_x, inner_y, inner_w, inner_h, BATTLE_HP_BAR_EMPTY_COLOR)
        hp_now = _clamp(player_hp, 0, PLAYER_HP_MAX)
        fill_w = 0
        if PLAYER_HP_MAX > 0:
            fill_w = (inner_w * hp_now) // PLAYER_HP_MAX
        if fill_w > 0:
            _fill_rect_solid(inner_x, inner_y, fill_w, inner_h, BATTLE_HP_BAR_FILL_COLOR)

    right_x = bar_x + bar_w + BATTLE_HP_BAR_GAP
    _draw_bold_text(right_x, y, right_text)


def _clear_battle_status_line_menu():
    y = menu_cmd_y_used - (8 + BATTLE_STATUS_TO_CMD_GAP)
    x = menu_frame_x_used + 8
    w = menu_frame_w_used - 16
    # Only clear the status-line band; never overlap the command button row.
    h = 10
    max_h = menu_cmd_y_used - y - 1
    if max_h < 1:
        return
    if h > max_h:
        h = max_h
    _clear_rect_black(x, y, w, h)


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
                player_hp = PLAYER_HP_MAX
                mode = MODE_EXPLORE
                encounter_cooldown_frames = ENCOUNTER_COOLDOWN_FRAMES
                _clear_act_dialog_state(True)
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
    global battle_dialog_mode, mercy_exit_pending, battle_dialog_started_ms, battle_dialog_png_info, battle_dialog_text
    global explore_force_full_redraw, fight_heart_x, fight_heart_y
    global battle_menu_dirty, battle_fight_dirty, battle_heart_needs_sprite_refresh, fight_return_deadline_ms
    global act_menu_active, act_choice_index, act_sequence_step, act_nav_prev_dir
    global act_prev_selected_index, act_selection_dirty, act_menu_slot_cache
    global item_menu_active, item_choice_index, item_nav_prev_dir, item_menu_slot_cache
    global item_prev_selected_index, item_selection_dirty, item_view_offset

    dialog_active = time.ticks_diff(act_dialog_until_ms, loop_start) > 0
    if mercy_exit_pending and not dialog_active:
        mode = MODE_EXPLORE
        encounter_cooldown_frames = ENCOUNTER_COOLDOWN_FRAMES
        _clear_act_dialog_state(True)
        mercy_exit_pending = False
        explore_force_full_redraw = True
        battle_menu_dirty = True
        return
    if dialog_active:
        return
    if battle_dialog_mode != BATTLE_DIALOG_NONE and not act_menu_active and not item_menu_active:
        battle_dialog_mode = BATTLE_DIALOG_NONE
        battle_dialog_png_info = None
        battle_dialog_text = None

    if item_menu_active:
        if fight_pressed:
            _reset_item_menu_state()
            battle_dialog_mode = BATTLE_DIALOG_NONE
            battle_dialog_png_info = None
            battle_dialog_text = None
            mode = MODE_BATTLE_FIGHT
            fight_heart_x = battle_heart_init_x
            fight_heart_y = battle_heart_init_y
            battle_fight_dirty = True
            battle_heart_needs_sprite_refresh = False
            fight_return_deadline_ms = time.ticks_add(loop_start, FIGHT_AUTO_RETURN_MS)
            battle_menu_dirty = True
            print("FIGHT")
            return
        if act_pressed:
            _reset_item_menu_state()
            act_menu_active = True
            act_choice_index = 0
            act_nav_prev_dir = 0
            act_prev_selected_index = -1
            act_selection_dirty = False
            battle_dialog_mode = BATTLE_DIALOG_ACT_OPTIONS
            battle_dialog_png_info = None
            battle_dialog_text = None
            battle_menu_dirty = True
            return
        if mercy_pressed:
            _reset_item_menu_state()
            if act_sequence_step == 3:
                print("MERCY: success")
                battle_dialog_mode = BATTLE_DIALOG_MERCY_EXIT
                battle_dialog_png_info = MERCY_SUCCESS_PNG_INFO
                battle_dialog_text = None
                act_dialog_until_ms = time.ticks_add(loop_start, MERCY_DIALOG_MS)
                battle_dialog_started_ms = loop_start
                mercy_exit_pending = True
            else:
                print("MERCY: locked")
                battle_dialog_mode = BATTLE_DIALOG_MERCY_LOCKED
                battle_dialog_png_info = MERCY_LOCKED_PNG_INFO
                battle_dialog_text = None
                act_dialog_until_ms = time.ticks_add(loop_start, ACT_REPLY_MS)
                battle_dialog_started_ms = loop_start
                mercy_exit_pending = False
            battle_menu_dirty = True
            return

        if inventory_is_empty():
            _reset_item_menu_state()
            battle_dialog_mode = BATTLE_DIALOG_ITEM_RESULT
            battle_dialog_png_info = None
            battle_dialog_text = "No items"
            act_dialog_until_ms = time.ticks_add(loop_start, ITEM_REPLY_MS)
            battle_dialog_started_ms = loop_start
            battle_menu_dirty = True
            return

        nav_dir = _menu_nav_dir_vertical()
        if nav_dir != 0 and nav_dir != item_nav_prev_dir:
            prev_choice = item_choice_index
            count = len(inventory_items)
            if nav_dir > 0:
                item_choice_index = (item_choice_index + 1) % count
            else:
                item_choice_index = (item_choice_index + count - 1) % count
            if item_choice_index != prev_choice:
                item_selection_dirty = True
                battle_menu_dirty = True
        item_nav_prev_dir = nav_dir
        if item_pressed:
            item_choice_index = inventory_clamp_index(item_choice_index)
            result_text = _use_battle_item_at(item_choice_index)
            _reset_item_menu_state()
            item_choice_index = inventory_clamp_index(item_choice_index)
            item_view_offset = 0
            battle_dialog_mode = BATTLE_DIALOG_ITEM_RESULT
            battle_dialog_png_info = None
            battle_dialog_text = result_text
            act_dialog_until_ms = time.ticks_add(loop_start, ITEM_REPLY_MS)
            battle_dialog_started_ms = loop_start
            battle_menu_dirty = True
        return

    if act_menu_active:
        if fight_pressed:
            act_menu_active = False
            act_nav_prev_dir = 0
            act_menu_slot_cache = None
            act_prev_selected_index = -1
            act_selection_dirty = False
            battle_dialog_mode = BATTLE_DIALOG_NONE
            battle_dialog_png_info = None
            battle_dialog_text = None
            mode = MODE_BATTLE_FIGHT
            fight_heart_x = battle_heart_init_x
            fight_heart_y = battle_heart_init_y
            battle_fight_dirty = True
            battle_heart_needs_sprite_refresh = False
            fight_return_deadline_ms = time.ticks_add(loop_start, FIGHT_AUTO_RETURN_MS)
            battle_menu_dirty = True
            print("FIGHT")
            return
        if item_pressed:
            act_menu_active = False
            act_nav_prev_dir = 0
            act_menu_slot_cache = None
            act_prev_selected_index = -1
            act_selection_dirty = False
            if inventory_is_empty():
                _reset_item_menu_state()
                battle_dialog_mode = BATTLE_DIALOG_ITEM_RESULT
                battle_dialog_png_info = None
                battle_dialog_text = "No items"
                act_dialog_until_ms = time.ticks_add(loop_start, ITEM_REPLY_MS)
                battle_dialog_started_ms = loop_start
            else:
                item_menu_active = True
                item_choice_index = inventory_clamp_index(item_choice_index)
                item_nav_prev_dir = 0
                item_menu_slot_cache = None
                item_prev_selected_index = -1
                item_selection_dirty = False
                item_view_offset = 0
                battle_dialog_mode = BATTLE_DIALOG_NONE
                battle_dialog_png_info = None
                battle_dialog_text = None
            battle_menu_dirty = True
            return
        if mercy_pressed:
            act_menu_active = False
            act_nav_prev_dir = 0
            act_menu_slot_cache = None
            act_prev_selected_index = -1
            act_selection_dirty = False
            if act_sequence_step == 3:
                print("MERCY: success")
                battle_dialog_mode = BATTLE_DIALOG_MERCY_EXIT
                battle_dialog_png_info = MERCY_SUCCESS_PNG_INFO
                battle_dialog_text = None
                act_dialog_until_ms = time.ticks_add(loop_start, MERCY_DIALOG_MS)
                battle_dialog_started_ms = loop_start
                mercy_exit_pending = True
            else:
                print("MERCY: locked")
                battle_dialog_mode = BATTLE_DIALOG_MERCY_LOCKED
                battle_dialog_png_info = MERCY_LOCKED_PNG_INFO
                battle_dialog_text = None
                act_dialog_until_ms = time.ticks_add(loop_start, ACT_REPLY_MS)
                battle_dialog_started_ms = loop_start
                mercy_exit_pending = False
            battle_menu_dirty = True
            return

        nav_dir = 0
        if x_dir > 0:
            nav_dir = 1
        elif x_dir < 0:
            nav_dir = -1
        if nav_dir != 0 and nav_dir != act_nav_prev_dir:
            prev_choice = act_choice_index
            if nav_dir > 0:
                act_choice_index = (act_choice_index + 1) % 3
            else:
                act_choice_index = (act_choice_index + 2) % 3
            if act_choice_index != prev_choice:
                act_selection_dirty = True
        act_nav_prev_dir = nav_dir
        if act_pressed:
            selected = act_choice_index
            if selected == 0:
                if act_sequence_step == 0:
                    act_sequence_step = 1
                else:
                    act_sequence_step = 0
                battle_dialog_png_info = ACT_REPLY_PNG_INFOS[0]
            elif selected == 1:
                if act_sequence_step == 1:
                    act_sequence_step = 2
                else:
                    act_sequence_step = 0
                battle_dialog_png_info = ACT_REPLY_PNG_INFOS[1]
            else:
                if act_sequence_step == 2:
                    act_sequence_step = 3
                else:
                    act_sequence_step = 0
                battle_dialog_png_info = ACT_REPLY_PNG_INFOS[2]
            act_menu_active = False
            act_nav_prev_dir = 0
            act_menu_slot_cache = None
            act_prev_selected_index = -1
            act_selection_dirty = False
            battle_dialog_mode = BATTLE_DIALOG_ACT_REPLY
            battle_dialog_started_ms = loop_start
            act_dialog_until_ms = time.ticks_add(loop_start, ACT_REPLY_MS)
            battle_dialog_text = None
            battle_menu_dirty = True
        return

    if fight_pressed:
        mode = MODE_BATTLE_FIGHT
        fight_heart_x = battle_heart_init_x
        fight_heart_y = battle_heart_init_y
        battle_fight_dirty = True
        battle_heart_needs_sprite_refresh = False
        fight_return_deadline_ms = time.ticks_add(loop_start, FIGHT_AUTO_RETURN_MS)
        battle_dialog_text = None
        print("FIGHT")
        return
    if act_pressed:
        act_menu_active = True
        act_choice_index = 0
        act_nav_prev_dir = 0
        act_prev_selected_index = -1
        act_selection_dirty = False
        battle_dialog_mode = BATTLE_DIALOG_ACT_OPTIONS
        battle_dialog_png_info = None
        battle_dialog_text = None
        mercy_exit_pending = False
        battle_menu_dirty = True
        return
    if item_pressed:
        if inventory_is_empty():
            battle_dialog_mode = BATTLE_DIALOG_ITEM_RESULT
            battle_dialog_png_info = None
            battle_dialog_text = "No items"
            act_dialog_until_ms = time.ticks_add(loop_start, ITEM_REPLY_MS)
            battle_dialog_started_ms = loop_start
            battle_menu_dirty = True
            return
        _reset_item_menu_state()
        item_menu_active = True
        item_choice_index = inventory_clamp_index(item_choice_index)
        item_nav_prev_dir = 0
        item_view_offset = 0
        battle_dialog_mode = BATTLE_DIALOG_NONE
        battle_dialog_png_info = None
        battle_dialog_text = None
        battle_menu_dirty = True
        return
    if mercy_pressed:
        if act_sequence_step == 3:
            print("MERCY: success")
            battle_dialog_mode = BATTLE_DIALOG_MERCY_EXIT
            battle_dialog_png_info = MERCY_SUCCESS_PNG_INFO
            battle_dialog_text = None
            act_dialog_until_ms = time.ticks_add(loop_start, MERCY_DIALOG_MS)
            battle_dialog_started_ms = loop_start
            mercy_exit_pending = True
        else:
            print("MERCY: locked")
            battle_dialog_mode = BATTLE_DIALOG_MERCY_LOCKED
            battle_dialog_png_info = MERCY_LOCKED_PNG_INFO
            battle_dialog_text = None
            act_dialog_until_ms = time.ticks_add(loop_start, ACT_REPLY_MS)
            battle_dialog_started_ms = loop_start
            mercy_exit_pending = False
        battle_menu_dirty = True


def update_battle_fight(loop_start):
    global mode, fight_heart_x, fight_heart_y
    global battle_menu_dirty, battle_dialog_visible, fight_return_deadline_ms
    global battle_fight_dirty, battle_bullets_dirty, battle_status_dirty
    global battle_dialog_mode, mercy_exit_pending, battle_dialog_png_info, battle_dialog_text, act_dialog_until_ms
    global battle_menu_full_clear_pending, battle_menu_static_ready, battle_menu_prev_dialog_active
    global act_menu_active, act_nav_prev_dir
    global item_menu_active, item_nav_prev_dir
    global bullets, next_bullet_spawn_ms, damage_invuln_until_ms, battle_prev_bullet_positions

    if time.ticks_diff(fight_return_deadline_ms, loop_start) <= 0:
        mode = MODE_BATTLE_MENU
        battle_menu_dirty = True
        battle_dialog_visible = False
        battle_menu_full_clear_pending = True
        battle_menu_static_ready = False
        battle_menu_prev_dialog_active = False
        bullets = []
        next_bullet_spawn_ms = 0
        damage_invuln_until_ms = 0
        battle_prev_bullet_positions = []
        battle_bullets_dirty = False
        battle_status_dirty = True
        battle_dialog_mode = BATTLE_DIALOG_NONE
        battle_dialog_png_info = None
        battle_dialog_text = None
        act_dialog_until_ms = 0
        act_menu_active = False
        act_nav_prev_dir = 0
        _reset_item_menu_state()
        item_menu_active = False
        item_nav_prev_dir = 0
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
    global spawn_intro_needs_redraw
    global battle_prev_heart_x, battle_prev_heart_y
    global battle_menu_dirty, battle_fight_dirty, battle_dialog_visible, battle_heart_needs_sprite_refresh
    global battle_bullets_dirty, battle_prev_bullet_positions
    global battle_status_dirty
    global act_selection_dirty, act_prev_selected_index
    global item_selection_dirty
    global inv_screen_dirty

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
        if spawn_intro_active:
            if scene_redrawn or dialog_needs_redraw:
                spawn_intro_needs_redraw = True
            if spawn_intro_needs_redraw:
                _draw_spawn_intro_overlay()
                spawn_intro_needs_redraw = False
        prev_player_x = player_x
        prev_player_y = player_y
        prev_scroll_x = scroll_x
        prev_scroll_y = scroll_y
        return

    if mode == MODE_EXPLORE_INVENTORY:
        if inv_screen_dirty:
            _draw_explore_inventory_screen()
            inv_screen_dirty = False
        return

    if mode == MODE_BATTLE_MENU:
        dialog_active = act_menu_active or item_menu_active or (time.ticks_diff(act_dialog_until_ms, loop_start) > 0)
        if battle_menu_dirty or dialog_active != battle_dialog_visible:
            _draw_battle_menu_screen(dialog_active)
            battle_menu_dirty = False
            battle_dialog_visible = dialog_active
            act_selection_dirty = False
            item_selection_dirty = False
        elif act_selection_dirty and act_menu_active and act_menu_slot_cache:
            _draw_act_selection_indicator(act_prev_selected_index, act_choice_index, act_menu_slot_cache)
            act_prev_selected_index = act_choice_index
            act_selection_dirty = False
        if dialog_active:
            _clear_battle_status_line_menu()
        else:
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
    # Slowly retune center while stick is neutral to avoid long-term drift/sticky axis.
    neutral = axis_max // DEADZONE_DIV
    if x_dir == 0:
        dx_center = rx - cx
        dx_mid = rx - (axis_max // 2)
        if (-neutral <= dx_center <= neutral) or (-neutral <= dx_mid <= neutral):
            cx = ((cx * 15) + rx) // 16
    if y_dir_raw == 0:
        dy_center = ry - cy
        dy_mid = ry - (axis_max // 2)
        if (-neutral <= dy_center <= neutral) or (-neutral <= dy_mid <= neutral):
            cy = ((cy * 15) + ry) // 16

    x_dir = _axis_dir(rx, cx, axis_max, x_dir)
    y_dir_raw = _axis_dir(ry, cy, axis_max, y_dir_raw)

    # Robust intro-exit gate: clear on stick deflection even before axis dir hysteresis engages.
    if spawn_intro_active:
        intro_neutral = axis_max // DEADZONE_DIV
        if (rx - cx) > intro_neutral or (rx - cx) < -intro_neutral or (ry - cy) > intro_neutral or (ry - cy) < -intro_neutral:
            spawn_intro_active = False
            spawn_intro_cleared_once = True
            explore_force_full_redraw = True

    interact_sw_prev, interact_pressed = _read_falling_edge(interact_sw, interact_sw_prev)
    btn_fight_prev, fight_pressed = _read_falling_edge(btn_fight, btn_fight_prev)
    btn_act_prev, act_pressed = _read_falling_edge(btn_act, btn_act_prev)
    btn_item_prev, item_pressed = _read_falling_edge(btn_item, btn_item_prev)
    btn_mercy_prev, mercy_pressed = _read_falling_edge(btn_mercy, btn_mercy_prev)

    if mode == MODE_EXPLORE:
        update_player(loop_start, frame_dt)

        if mode == MODE_EXPLORE and item_pressed:
            _open_explore_inventory()

        if mode == MODE_EXPLORE:
            _update_preload_for_player(player_x, player_y)

            if teleport_cooldown_frames == 0:
                active_portal = _get_current_portal(player_x, player_y)
                if active_portal:
                    target_spawn = active_portal.get("target_spawn")
                    if target_spawn and len(target_spawn) >= 2:
                        switch_map(active_portal["target_map_id"], target_spawn[0], target_spawn[1])
                    else:
                        switch_map(active_portal["target_map_id"])

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
    elif mode == MODE_EXPLORE_INVENTORY:
        explore_moved = False
        explore_scrolled = False
        explore_anim_changed = False
        update_explore_inventory(loop_start, item_pressed, interact_pressed)
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
