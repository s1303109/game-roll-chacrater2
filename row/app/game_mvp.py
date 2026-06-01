import gc
import json
import os
import time
from machine import ADC, Pin
import lgfx
import config
from map_registry import (
    MAP1_ID,
    MAP2_ID,
    MAP3_ID,
    MAP4_ID,
    MAP5_ID,
    MAP6_ID,
    MAP8_ID,
    WOOD_MAIN_ID,
    WOOD_UP_ID,
    WOOD_RIGHT_ID,
    WOOD_LEFT_ID,
    MAP_REGISTRY,
)


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
        # Avoid selecting a base that has map.json but incomplete/corrupt tile files.
        tile = meta.get("tile_size", 0)
        map_w = meta.get("map_w", 0)
        map_h = meta.get("map_h", 0)
        if tile <= 0 or map_w <= 0 or map_h <= 0:
            continue
        expected_tilemap = map_w * map_h * 2
        tile_bytes = tile * tile * 2
        try:
            tilemap_size = os.stat(base + "/tilemap.bin")[6]
            tileset_size = os.stat(base + "/tileset.bin")[6]
        except OSError:
            continue
        if tilemap_size != expected_tilemap:
            continue
        if tile_bytes <= 0 or tileset_size <= 0 or (tileset_size % tile_bytes) != 0:
            continue
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


def _ui_asset_paths(name):
    return (config.ui_path(name),)


def _resolve_runtime_png_path(path):
    if not path:
        return None
    if _path_exists(path):
        return path
    name = path.rsplit("/", 1)[-1]
    if not name:
        return path
    resolved = config.ui_path(name)
    if _path_exists(resolved):
        return resolved
    return path


def _sync_sd_assets_from_remote_if_needed():
    return


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

    bases = [base]

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
            if mode < 2:
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


def _switch_map_direct_fallback(target_map_id, target_record, spawn_x=None, spawn_y=None):
    global collision, meta, asset_base, current_map_id
    global player_x, player_y, scroll_x, scroll_y
    global prev_scroll_x, prev_scroll_y, prev_player_x, prev_player_y
    global leaf_zone_prev_inside, explore_overlay_dirty, lamp_dialog_until_ms
    global explore_force_full_redraw, teleport_cooldown_frames
    global tile, map_w, map_h, world_w, world_h, runtime_endian
    global move_carry_x, move_carry_y, prev_input_x, prev_input_y
    global preload_suspend_until_ms, gc_suspend_until_ms, gc_pending
    global resident_back_slot_id, resident_active_slot_id, resident_ahead_slot_id
    global preload_zone_target_map_id, preload_zone_enter_ms

    try:
        _release_preload_cache("switch_direct_fallback")
        _resident_release_slot(resident_back_slot_id, "switch_direct_release_back")
        _resident_release_slot(resident_ahead_slot_id, "switch_direct_release_ahead")

        asset_base = target_record["asset_base"]
        meta = target_record["meta"]
        collision = target_record["collision"]
        tile = meta["tile_size"]
        map_w = meta["map_w"]
        map_h = meta["map_h"]
        world_w = map_w * tile
        world_h = map_h * tile
        _tile_setup_with_fallback()
        runtime_endian = _load_tiles(meta, asset_base, tile, map_w, map_h, prefer_stream=True)
        if hasattr(lgfx, "set_swap_bytes"):
            lgfx.set_swap_bytes(runtime_endian == "little")
    except Exception as err:
        print("switch_map_direct_fail:", err)
        return False

    if spawn_x is None and target_record.get("spawn") and len(target_record["spawn"]) >= 2:
        spawn_x = target_record["spawn"][0]
    if spawn_y is None and target_record.get("spawn") and len(target_record["spawn"]) >= 2:
        spawn_y = target_record["spawn"][1]

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
    move_carry_x = 0
    move_carry_y = 0
    prev_input_x = 0
    prev_input_y = 0

    leaf_zone_prev_inside = False
    explore_overlay_dirty = False
    lamp_dialog_until_ms = 0
    explore_force_full_redraw = True
    teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
    current_map_id = target_map_id
    _encounter_on_map_enter(current_map_id)

    role_active = resident_slots[resident_active_slot_id]["role"]
    resident_slots[resident_active_slot_id].update(target_record)
    resident_slots[resident_active_slot_id]["role"] = role_active
    _resident_clear_slot_record(resident_back_slot_id)
    _resident_clear_slot_record(resident_ahead_slot_id)
    _resident_sync_roles()

    preload_zone_target_map_id = None
    preload_zone_enter_ms = 0
    now = time.ticks_ms()
    preload_suspend_until_ms = time.ticks_add(now, PRELOAD_POST_SWITCH_PAUSE_MS)
    gc_suspend_until_ms = time.ticks_add(now, GC_POST_SWITCH_PAUSE_MS)
    if GC_DEFER_ENABLE:
        gc_pending = True
    else:
        gc.collect()
    print("switch_map_direct_ok:", target_map_id)
    return True


def _switch_map_boot_fallback(target_map_id, target_record, spawn_x=None, spawn_y=None):
    global current_map_id
    global player_x, player_y, scroll_x, scroll_y
    global prev_scroll_x, prev_scroll_y, prev_player_x, prev_player_y
    global leaf_zone_prev_inside, explore_overlay_dirty, lamp_dialog_until_ms
    global explore_force_full_redraw, teleport_cooldown_frames
    global move_carry_x, move_carry_y, prev_input_x, prev_input_y
    global preload_suspend_until_ms, gc_suspend_until_ms, gc_pending
    global preload_zone_target_map_id, preload_zone_enter_ms

    try:
        _release_preload_cache("switch_boot_fallback")
        _resident_boot_activate_map(target_map_id)
    except Exception as err:
        print("switch_map_boot_fail:", err)
        return False

    if spawn_x is None and target_record.get("spawn") and len(target_record["spawn"]) >= 2:
        spawn_x = target_record["spawn"][0]
    if spawn_y is None and target_record.get("spawn") and len(target_record["spawn"]) >= 2:
        spawn_y = target_record["spawn"][1]

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
    move_carry_x = 0
    move_carry_y = 0
    prev_input_x = 0
    prev_input_y = 0

    leaf_zone_prev_inside = False
    explore_overlay_dirty = False
    lamp_dialog_until_ms = 0
    explore_force_full_redraw = True
    teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
    current_map_id = target_map_id
    _encounter_on_map_enter(current_map_id)

    preload_zone_target_map_id = None
    preload_zone_enter_ms = 0
    now = time.ticks_ms()
    preload_suspend_until_ms = time.ticks_add(now, PRELOAD_POST_SWITCH_PAUSE_MS)
    gc_suspend_until_ms = time.ticks_add(now, GC_POST_SWITCH_PAUSE_MS)
    if GC_DEFER_ENABLE:
        gc_pending = True
    else:
        gc.collect()
    print("switch_map_boot_ok:", target_map_id)
    return True


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

    _add_path(PLAYER_SHEET_PATH)

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


def _load_map6_boss_sheet():
    if (
        (not hasattr(lgfx, "enemy_sheet_load_file"))
        or (not hasattr(lgfx, "enemy_frame_set"))
        or (not hasattr(lgfx, "enemy_sheet_clear"))
        or (not hasattr(lgfx, "enemy_draw"))
    ):
        print("map6_boss_sheet_api_missing")
        return False

    lgfx.enemy_sheet_clear()
    path = MAP6_BOSS_SHEET_PATH
    if not _path_exists(path):
        print("map6_boss_sheet_missing:", path)
        return False
    ok = bool(
        lgfx.enemy_sheet_load_file(
            path,
            MAP6_BOSS_SHEET_W,
            MAP6_BOSS_SHEET_H,
            MAP6_BOSS_FRAME_W,
            MAP6_BOSS_FRAME_H,
        )
    )
    if ok:
        lgfx.enemy_frame_set(0)
        print("map6_boss_sheet_loaded:", path)
        return True
    print("map6_boss_sheet_load_fail:", path)
    return False


MAP1_ASSET_BASES = MAP_REGISTRY[MAP1_ID]["asset_bases"]
ENABLE_SD_MOUNT = True
PLAYER_SHEET_NAME = config.PLAYER_SHEET_NAME
PLAYER_SHEET_PATH = config.PLAYER_SHEET_PATH
ENABLE_SPAWN_OVERLAY = False
SPAWN_OVERLAY_PATH = config.ui_path("main character close eyes.orig.png")
ENABLE_SPAWN_INTRO = True
SPAWN_SPOTLIGHT_RADIUS = 56
SPAWN_OVERLAY_PATHS = (
    config.ui_path("main character close eyes.clean.png"),
    config.ui_path("main character close eyes.orig.png"),
)
PORTAL_TRANSITION_EFFECT_SPOTLIGHT = "spotlight_shrink"
PORTAL_TRANSITION_DEFAULT_SHRINK_MS = 4000
PORTAL_TRANSITION_DEFAULT_BLACK_MS = 1000
PORTAL_TRANSITION_SWITCH_RETRY_MS = 250
PORTAL_TRANSITION_SWITCH_MAX_RETRY = 24
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
BINARY_EDGE_DEBOUNCE_MS = 45
MOVE_STEP = 2
WOOD_ROOM_MOVE_STEP = 1.4
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
WOOD_PLAYER_ANIM_STEP_MS = 180
ANIM_IDLE_HOLD_MS = 90
PLAYER_ANIM_ROW_FRONT = 0
PLAYER_ANIM_ROW_SIDE = 1
MODE_EXPLORE = 0
MODE_BATTLE_MENU = 1
MODE_BATTLE_FIGHT = 2
MODE_EXPLORE_INVENTORY = 3
MODE_BATTLE_ATTACK = 4
MODE_TITLE_MENU = 5
TITLE_COVER_PATHS = (
    config.ui_path("front_cover_320x240.png"),
)
TITLE_NOTICE_MS = 1200
TITLE_NAV_SWITCH_COOLDOWN_MS = 140
TITLE_MENU_CONTINUE = "CONTINUE"
TITLE_MENU_NEW_GAME = "NEW GAME"
TITLE_NOTICE_CONTINUE_TEXT = "Continue unavailable"
TITLE_NOTICE_NO_SAVE_TEXT = "No save found"
TITLE_UI_START_PATHS = _ui_asset_paths("title_ui_start_112x54.png")
TITLE_UI_CONTINUE_PATHS = _ui_asset_paths("title_ui_continue_112x54.png")
TITLE_UI_X = 8
TITLE_UI_W = 112
TITLE_UI_H = 54
TITLE_UI_Y = 150
TITLE_OPTION_NEW_GAME_RECT = (TITLE_UI_X, TITLE_UI_Y, TITLE_UI_W, 27)
TITLE_OPTION_CONTINUE_RECT = (TITLE_UI_X, TITLE_UI_Y + 27, TITLE_UI_W, 27)
BOOT_COMIC_TIME_LABELS = ("21:00", "23:00", "1:00", "00:00", "00:00", "00:00")
BOOT_TIME_CARD_MS = 3000
BOOT_COMIC_FRAME_MS = 5000
BOOT_COMIC_PATHS = (
    config.ui_path("comic_01_320x240.png"),
    config.ui_path("comic_02_320x240.png"),
    config.ui_path("comic_03_320x240.png"),
    config.ui_path("comic_04_320x240.png"),
    config.ui_path("comic_05_320x240.png"),
    config.ui_path("comic_06_320x240.png"),
)
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
BATTLE_HEART_SPRITE_PATH = config.ui_path("heart_clean_18.png")
BATTLE_HEART_SPRITE_FALLBACK_PATH = config.ui_path("heart.png")
BATTLE_HEART_SPRITE_W = 18
BATTLE_HEART_SPRITE_H = 18
BATTLE_HEART_HIT_R = 9
BATTLE_HEART_ERASE_R = BATTLE_HEART_HIT_R + 1
BATTLE_HEART_FAST_R = 7
BATTLE_HEART_STEP = 2
BATTLE_HEART_USE_PNG_ON_MOVE = False
ENEMY_SPRITE_PATH = config.ui_path("enemy.png")
ENEMY_SPRITE_W = 72
ENEMY_SPRITE_H = 72
MAP6_BOSS_BATTLE_SPRITE_PATH = config.ui_path("map6_boss_battle.png")
MAP6_BOSS_SHEET_PATH = config.sprite_path("map6_boss_sheet.rgb565")
MAP6_BOSS_SHEET_W = 576
MAP6_BOSS_SHEET_H = 576
MAP6_BOSS_FRAME_W = 192
MAP6_BOSS_FRAME_H = 192
MAP6_BOSS_CENTER_X = 548
MAP6_BOSS_CENTER_Y = 246
MAP6_BOSS_TRIGGER_RADIUS_PX = 54
MAP6_BOSS_ANIM_FRAME_MS = 300
MAP6_BOSS_ANIM_SEQUENCE = (0, 1, 2, 3, 4, 5, 6, 7, 8)
ACT_DIALOG_TEXT_PATH = config.ui_path("act_dialog_text.png")
MERCY_DIALOG_TEXT_PATH = config.ui_path("mercy_dialog_text.png")
LAMP_DIALOG_TEXT_PATH = config.ui_path("lamp_dialog_text.png")
ACT_OPT1_PNG = config.ui_path("act_opt1_text.png")
ACT_OPT2_PNG = config.ui_path("act_opt2_text.png")
ACT_OPT3_PNG = config.ui_path("act_opt3_text.png")
ACT_REPLY1_PNG = config.ui_path("act_reply1_text.png")
ACT_REPLY2_PNG = config.ui_path("act_reply2_text.png")
ACT_REPLY3_PNG = config.ui_path("act_reply3_text.png")
MERCY_LOCKED_PNG = config.ui_path("mercy_locked_text.png")
CMD_ICON_SRC_W = 32
CMD_ICON_SRC_H = 32
STAR_ICON_SRC_W = 24
STAR_ICON_SRC_H = 24
STAR_ICON_PATHS = (config.ui_path("star_icon_24.png"),)
INVENTORY_PORTRAIT_PATHS = (config.ui_path("inventory_portrait.png"),)
INVENTORY_PORTRAIT_SRC_W = 255
INVENTORY_PORTRAIT_SRC_H = 221
FIGHT_ICON_PATHS = _ui_asset_paths("fight_icon.png")
ACT_ICON_PATHS = _ui_asset_paths("act_icon.png")
ITEM_ICON_PATHS = _ui_asset_paths("item_icon.png")
MERCY_ICON_PATHS = _ui_asset_paths("mercy_icon.png")
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
MAP1_OPENING_BATTLE_DELAY_MS = 5000
# Expand to cover the full triple-lamp poles and nearby interaction area.
LAMP_INTERACT_RECT_PX = (160, 624, 128, 192)
# Apply slow movement only in the main wood room.
WOOD_SLOW_MAP_IDS = (WOOD_MAIN_ID,)
MAP1_SPAWN_OFFSET_X = 0
MAP1_SPAWN_OFFSET_Y = -63
PRELOAD_PORTAL_PAD_PX = 32
PRELOAD_DEBOUNCE_PX = 8
PRELOAD_DWELL_MS = 220
PRELOAD_COOLDOWN_MS = 350
PRELOAD_RELEASE_GRACE_MS = 500
PRELOAD_POST_SWITCH_PAUSE_MS = 1200
# Fast-track preload for selected return targets (to reduce backtrack wait).
PRELOAD_FAST_TRACK_TARGET_MAP_IDS = (MAP1_ID,)
GC_DEFER_ENABLE = True
GC_DEFER_MIN_INTERVAL_MS = 900
GC_DEFER_IDLE_ONLY = True
GC_POST_SWITCH_PAUSE_MS = 1500
DEBUG_PERF = False
TELEPORT_COOLDOWN_FRAMES = 30
LAMP_DIALOG_TEXT_W = 214
LAMP_DIALOG_TEXT_H = 27
ACT_DIALOG_MS = 1000
MERCY_DIALOG_MS = 2500
LAMP_DIALOG_MS = 2000
ITEM_REPLY_MS = 1000
MAP1_STORY_LINE_MS = 4000
MAP1_STORY_ENEMY_SLIDE_MS = 300
MAP1_STORY_STAGE_NONE = 0
MAP1_STORY_STAGE_INTRO_LINES = 1
MAP1_STORY_STAGE_PHASE1 = 2
MAP1_STORY_STAGE_MID_LINES = 3
MAP1_STORY_STAGE_PHASE2 = 4
MAP1_STORY_PHASE2_EVENT_NONE = 0
MAP1_STORY_PHASE2_EVENT_PAUSE = 1
MAP1_STORY_PHASE2_EVENT_FIRE_FLY = 2
MAP1_STORY_PHASE2_EVENT_FIRE_HOLD = 3
MAP1_STORY_PHASE2_EVENT_TORIEL_SLIDE = 4
MAP1_STORY_PHASE2_EVENT_TORIEL_LINES = 5
MAP1_STORY_PHASE2_NEAR_HIT_PAD_PX = 12
MAP1_STORY_PHASE2_FREEZE_MS = 4000
MAP1_STORY_FIRE_FLY_MS = 1800
MAP1_STORY_FIRE_HOLD_MS = 3000
MAP1_STORY_TORIEL_SLIDE_MS = 900
MAP1_STORY_FIRE_STEP_PX = 5
MAP1_STORY_TORIEL_STEP_PX = 4
MAP1_STORY_ANIM_STEP_MAX = 10
MAP1_STORY_DIALOG_LEFT_INSET = 14
MAP1_STORY_DIALOG_GAP_PX = 10
MAP1_STORY_TORIEL_TARGET_SHIFT_LEFT_PX = 0
MAP1_STORY_FIRE_HIT_OVERLAP_PX = 20
MAP1_STORY_FLOWEY_HIT_CONFIRM_LEFT_PX = 12
MAP1_ENEMY_ANCHOR_CENTER = 0
MAP1_ENEMY_ANCHOR_SLIDING_LEFT = 1
MAP1_ENEMY_ANCHOR_LEFT = 2
MAP1_FLOWEY_SPRITE_PATHS = _ui_asset_paths("FLOWEY.png")
MAP1_ANGRY_FLOWEY_SPRITE_PATHS = _ui_asset_paths("ANGRY FLOWEY.png")
MAP1_FLOWEY_ANIM_SPRITE_PATHS = (config.ui_path("FLOWEY_anim_96.png"),) + MAP1_FLOWEY_SPRITE_PATHS
MAP1_ANGRY_FLOWEY_ANIM_SPRITE_PATHS = (config.ui_path("ANGRY FLOWEY_anim_96.png"),) + MAP1_ANGRY_FLOWEY_SPRITE_PATHS
MAP1_FIRE_SPRITE_PATHS = (
    config.ui_path("fire ball small.png"),
    config.ui_path("fire ball_anim_64.png"),
) + _ui_asset_paths("fire ball.png")
MAP1_TORIEL_SPRITE_PATHS = (config.ui_path("kind people_anim_96.png"),) + _ui_asset_paths("kind people.png")
MAP1_STORY_LINE_PNG_PATHS = (
    _ui_asset_paths("map1_story_line_01.png"),
    _ui_asset_paths("map1_story_line_02.png"),
    _ui_asset_paths("map1_story_line_03.png"),
    _ui_asset_paths("map1_story_line_10.png"),
    _ui_asset_paths("map1_story_line_07.png"),
    _ui_asset_paths("map1_story_line_04.png"),
    _ui_asset_paths("map1_story_line_05.png"),
    _ui_asset_paths("map1_story_line_06.png"),
    _ui_asset_paths("map1_story_line_08.png"),
    _ui_asset_paths("map1_story_line_09.png"),
    _ui_asset_paths("map1_story_line_11.png"),
    _ui_asset_paths("map1_story_line_12.png"),
    _ui_asset_paths("map1_story_line_13.png"),
    _ui_asset_paths("map1_story_line_14.png"),
    _ui_asset_paths("map1_story_line_15.png"),
    _ui_asset_paths("map1_story_line_16.png"),
    _ui_asset_paths("map1_story_line_17.png"),
    _ui_asset_paths("map1_story_line_18.png"),
)
MAP1_STORY_LINE_PNG_W = 200
MAP1_STORY_LINE_PNG_H = 72
MAP1_STORY_LINE1_PNG_W = 200
MAP1_STORY_LINE1_PNG_H = 72
MAP1_STORY_ENEMY_DRAW_W = 96
MAP1_STORY_ENEMY_DRAW_H = 96
MAP1_STORY_PHASE1_BULLET_SPEED_PX = 2
MAP1_STORY_PHASE2_BULLET_SPEED_PX = 1
MAP1_STORY_FIRE_DRAW_W = 20
MAP1_STORY_FIRE_DRAW_H = 20
MAP1_STORY_TORIEL_DRAW_W = 96
MAP1_STORY_TORIEL_DRAW_H = 96
PLAYER_HP_MAX = 20
PLAYER_NAME = "OTIS"
PLAYER_LV = 1
PLAYER_WEAPON = "None"
PLAYER_ARMOR = "Bandage"
PLAYER_AT_BASE = 5
PLAYER_AT_BONUS = 0
PLAYER_DF_BASE = 5
PLAYER_DF_BONUS = 0
ENEMY_HP_MAX = 30
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
ATTACK_BAR_TIMEOUT_MS = 10000
ATTACK_BAR_W = 160
ATTACK_BAR_H = 12
ATTACK_CURSOR_W = 3
ATTACK_CURSOR_SPEED_PX = 4
ATTACK_BAR_Y_OFFSET = 34
ATTACK_ENEMY_DRAW_W = 42
ATTACK_ENEMY_DRAW_H = 42
ATTACK_BAR_BG_COLOR = 0x0000
ATTACK_BAR_OUTLINE_COLOR = 0xFFFF
ATTACK_BAR_BORDER_COLOR = 0xFFE0  # bright yellow
ATTACK_BAR_BORDER_INNER_COLOR = 0xAFE0  # yellow-green
ATTACK_BAR_LOW_ZONE_COLOR = 0xF800  # red
ATTACK_BAR_PERFECT_COLOR = 0x07E0  # bright green
ATTACK_BAR_PERFECT_CORE_COLOR = 0x57EA  # lighter green
ATTACK_BAR_TICK_COLOR = 0xFFE0  # yellow
ATTACK_BAR_DECOR_RED = 0xF800
ATTACK_BAR_DECOR_YELLOW = 0xFFE0
ATTACK_BAR_CURSOR_COLOR = 0xFFFF
ATTACK_BAR_CURSOR_SHADOW_COLOR = 0x4208
ATTACK_BAR_CURSOR_CORE_COLOR = 0xC618  # light gray
ATTACK_CURSOR_EXTRA_PX = 7
ATTACK_ZONE_PERFECT_PCT = 10
ATTACK_ZONE_GOOD_PCT = 35
ENEMY_HP_BAR_W = 120
ENEMY_HP_BAR_H = 8
ENEMY_HP_BAR_FILL_COLOR = 0x801F  # purple
ENEMY_HP_BAR_EMPTY_COLOR = 0xF800  # red
BUILD_TAG = "game_mvp_tune36_revert_tune33_heart_20260519"

print("build:", BUILD_TAG)

MAP_ENCOUNTER_PORTAL_SAFE_PAD_PX = 32
MAP_ENCOUNTER_ENTRY_MIN_TRAVEL_PX = 0
MAP_ENCOUNTER_ENTRY_GRACE_MIN_MS = 10000
MAP_ENCOUNTER_ENTRY_GRACE_MAX_MS = 15000
MAP_ENCOUNTER_PICK_MODE_ROUND_ROBIN = "round_robin"
DEFAULT_BATTLE_ENEMY_ID = "MAP1_FALLBACK_ENEMY"

ENEMY_REGISTRY = {
    "MAP1_FALLBACK_ENEMY": {
        "enemy_id": "MAP1_FALLBACK_ENEMY",
        "display_name": MONSTER_NAME,
        "sprite_path": ENEMY_SPRITE_PATH,
        "sprite_w": ENEMY_SPRITE_W,
        "sprite_h": ENEMY_SPRITE_H,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "It watches you."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "It stares silently."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "It loosens up."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
    "MAP2_ENEMY1": {
        "enemy_id": "MAP2_ENEMY1",
        "display_name": "MAP2 Enemy 1",
        "sprite_path": ENEMY_SPRITE_PATH,
        "sprite_w": ENEMY_SPRITE_W,
        "sprite_h": ENEMY_SPRITE_H,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "MAP2 Enemy 1 replies A."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "MAP2 Enemy 1 replies B."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "MAP2 Enemy 1 replies C."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
    "MAP2_ENEMY2": {
        "enemy_id": "MAP2_ENEMY2",
        "display_name": "MAP2 Enemy 2",
        "sprite_path": ENEMY_SPRITE_PATH,
        "sprite_w": ENEMY_SPRITE_W,
        "sprite_h": ENEMY_SPRITE_H,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "MAP2 Enemy 2 replies A."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "MAP2 Enemy 2 replies B."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "MAP2 Enemy 2 replies C."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
    "MAP3_ENEMY1": {
        "enemy_id": "MAP3_ENEMY1",
        "display_name": "MAP3 Enemy 1",
        "sprite_path": ENEMY_SPRITE_PATH,
        "sprite_w": ENEMY_SPRITE_W,
        "sprite_h": ENEMY_SPRITE_H,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "MAP3 Enemy 1 replies A."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "MAP3 Enemy 1 replies B."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "MAP3 Enemy 1 replies C."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
    "MAP3_ENEMY2": {
        "enemy_id": "MAP3_ENEMY2",
        "display_name": "MAP3 Enemy 2",
        "sprite_path": ENEMY_SPRITE_PATH,
        "sprite_w": ENEMY_SPRITE_W,
        "sprite_h": ENEMY_SPRITE_H,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "MAP3 Enemy 2 replies A."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "MAP3 Enemy 2 replies B."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "MAP3 Enemy 2 replies C."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
    "MAP4_ENEMY1": {
        "enemy_id": "MAP4_ENEMY1",
        "display_name": "MAP4 Enemy 1",
        "sprite_path": ENEMY_SPRITE_PATH,
        "sprite_w": ENEMY_SPRITE_W,
        "sprite_h": ENEMY_SPRITE_H,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "MAP4 Enemy 1 replies A."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "MAP4 Enemy 1 replies B."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "MAP4 Enemy 1 replies C."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
    "MAP4_ENEMY2": {
        "enemy_id": "MAP4_ENEMY2",
        "display_name": "MAP4 Enemy 2",
        "sprite_path": ENEMY_SPRITE_PATH,
        "sprite_w": ENEMY_SPRITE_W,
        "sprite_h": ENEMY_SPRITE_H,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "MAP4 Enemy 2 replies A."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "MAP4 Enemy 2 replies B."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "MAP4 Enemy 2 replies C."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
    "MAP6_BOSS": {
        "enemy_id": "MAP6_BOSS",
        "display_name": "MAP6 Boss",
        "sprite_path": MAP6_BOSS_BATTLE_SPRITE_PATH,
        "sprite_w": 96,
        "sprite_h": 96,
        "act_options": (
            {"png": ACT_OPT1_PNG, "png_w": 88, "png_h": 18, "text": "Observe"},
            {"png": ACT_OPT2_PNG, "png_w": 72, "png_h": 18, "text": "Question"},
            {"png": ACT_OPT3_PNG, "png_w": 64, "png_h": 18, "text": "Calm"},
        ),
        "act_replies": (
            {"png": ACT_REPLY1_PNG, "png_w": 132, "png_h": 18, "text": "It watches you."},
            {"png": ACT_REPLY2_PNG, "png_w": 168, "png_h": 18, "text": "It stares silently."},
            {"png": ACT_REPLY3_PNG, "png_w": 132, "png_h": 18, "text": "It loosens up."},
        ),
        "mercy_locked": {"png": MERCY_LOCKED_PNG, "png_w": 144, "png_h": 18, "text": "Cannot spare yet."},
        "mercy_success": {"png": MERCY_DIALOG_TEXT_PATH, "png_w": 220, "png_h": 20, "text": "Spared."},
    },
}

MAP_ENCOUNTER_CONFIG = {
    MAP2_ID: {
        "enabled": True,
        "quota_range": (1, 1),
        "enemy_ids": ("MAP2_ENEMY1",),
        "pick_mode": MAP_ENCOUNTER_PICK_MODE_ROUND_ROBIN,
    },
    MAP3_ID: {
        "enabled": True,
        "quota_range": (1, 1),
        "enemy_ids": ("MAP3_ENEMY1",),
        "pick_mode": MAP_ENCOUNTER_PICK_MODE_ROUND_ROBIN,
    },
    MAP4_ID: {
        "enabled": True,
        "quota_range": (1, 1),
        "enemy_ids": ("MAP4_ENEMY1",),
        "pick_mode": MAP_ENCOUNTER_PICK_MODE_ROUND_ROBIN,
    },
}

map_encounter_state = {}
for _encounter_map_id in MAP_ENCOUNTER_CONFIG:
    map_encounter_state[_encounter_map_id] = {
        "rolled_quota": None,
        "remaining": 0,
        "cleared": False,
        "enemy_cursor": 0,
        "entry_travel_px": 0,
        "entry_ready_after_ms": 0,
    }

current_battle_enemy = ENEMY_REGISTRY.get(DEFAULT_BATTLE_ENEMY_ID)
map6_boss_sheet_loaded = False
map6_boss_defeated = False
map6_boss_battle_active = False
map6_boss_anim_seq_index = 0
map6_boss_anim_last_ms = 0
map6_boss_last_draw_frame = -1
map6_boss_last_draw_sx = -99999
map6_boss_last_draw_sy = -99999

preload_zone_target_map_id = None
preload_zone_enter_ms = 0
preload_last_build_ms = 0
preload_last_release_ms = 0
preload_release_due_ms = 0
preload_suspend_until_ms = 0
portal_transition_active = False
portal_transition_started_ms = 0
portal_transition_stage = "none"
portal_transition_source_map_id = 0
portal_transition_target_map_id = 0
portal_transition_target_spawn = None
portal_transition_center_screen_x = 0
portal_transition_center_screen_y = 0
portal_transition_shrink_ms = PORTAL_TRANSITION_DEFAULT_SHRINK_MS
portal_transition_black_ms = PORTAL_TRANSITION_DEFAULT_BLACK_MS
portal_transition_portal_ref = None
portal_transition_last_switch_try_ms = 0
portal_transition_switch_fail_count = 0
portal_transition_rearm_required = False
portal_transition_rearm_map_id = 0
portal_transition_rearm_portal_ref = None
gc_pending = False
gc_last_run_ms = 0
gc_suspend_until_ms = 0
perf_preload_build_count = 0
perf_preload_build_fail_count = 0
perf_preload_build_ms_total = 0
perf_preload_release_count = 0
perf_preload_skip_cached = 0
perf_preload_skip_cooldown = 0
perf_preload_skip_debounce = 0
perf_preload_skip_dwell = 0
perf_preload_skip_same_zone = 0
perf_preload_skip_motion = 0
perf_preload_skip_post_switch = 0
perf_gc_run_count = 0
perf_gc_run_ms_total = 0

SLOT_ROLE_NONE = 0
SLOT_ROLE_BACK = 1
SLOT_ROLE_ACTIVE = 2
SLOT_ROLE_AHEAD = 3

SLOT_STATE_EMPTY = 0
SLOT_STATE_LOADING = 1
SLOT_STATE_READY = 2
SLOT_STATE_FAILED = 3

SLOT_STAGE_NONE = 0
SLOT_STAGE_VALIDATE = 1
SLOT_STAGE_ACQUIRE_TILESET = 2
SLOT_STAGE_WAIT_TILESET = 3
SLOT_STAGE_LOAD_TILESET = 4
SLOT_STAGE_LOAD_TILEMAP = 5
SLOT_STAGE_READY = 6

RESIDENT_SLOT_IDS = (0, 1, 2)
RESIDENT_BACK_SLOT_ID = 0
RESIDENT_ACTIVE_SLOT_ID = 1
RESIDENT_AHEAD_SLOT_ID = 2
PRELOAD_BUDGET_BYTES = 8192

resident_slots = {
    0: {"role": SLOT_ROLE_BACK, "map_id": None, "map_token": 0, "tileset_token": 0, "asset_base": None, "tile_base": None, "meta": None, "collision": None, "spawn": None},
    1: {"role": SLOT_ROLE_ACTIVE, "map_id": None, "map_token": 0, "tileset_token": 0, "asset_base": None, "tile_base": None, "meta": None, "collision": None, "spawn": None},
    2: {"role": SLOT_ROLE_AHEAD, "map_id": None, "map_token": 0, "tileset_token": 0, "asset_base": None, "tile_base": None, "meta": None, "collision": None, "spawn": None},
}
resident_back_slot_id = RESIDENT_BACK_SLOT_ID
resident_active_slot_id = RESIDENT_ACTIVE_SLOT_ID
resident_ahead_slot_id = RESIDENT_AHEAD_SLOT_ID
resident_transition_active = False

ITEM_HEAL_TEST = {
    "id": "heal_candy",
    "name": "Candy",
    "heal_amount": 6,
    "consumable": True,
}

WOOD_RIGHT_WEAPON_PICKUP_RADIUS = 18
GROUND_WEAPON_PICKUP_RADIUS = 10
GROUND_DROP_MARKER_R = 2

WEAPON_KNIFE = {
    "id": "weapon_knife",
    "name": "Knife",
    "item_type": "weapon",
    "equip_slot": "weapon",
    "at_bonus": 1,
    "df_bonus": 0,
    "heal_amount": 0,
    "consumable": False,
}
WEAPON_SWORD = {
    "id": "weapon_sword",
    "name": "Sword",
    "item_type": "weapon",
    "equip_slot": "weapon",
    "at_bonus": 2,
    "df_bonus": 0,
    "heal_amount": 0,
    "consumable": False,
}
WOOD_RIGHT_WEAPON_RACKS = (
    {
        "pickup_id": "wood_right_rack_knife",
        "map_id": WOOD_RIGHT_ID,
        "rect": (108, 34, 34, 60),
        "interact_x": 126,
        "interact_y": 92,
        "item": WEAPON_KNIFE,
    },
    {
        "pickup_id": "wood_right_rack_sword",
        "map_id": WOOD_RIGHT_ID,
        "rect": (194, 34, 40, 60),
        "interact_x": 214,
        "interact_y": 92,
        "item": WEAPON_SWORD,
    },
)
rack_pickup_taken = {
    "wood_right_rack_knife": False,
    "wood_right_rack_sword": False,
}
ground_weapon_drops = []
ground_weapon_drop_seq = 0
equipped_weapon_item_id = None
equipped_armor_item_id = None

inventory_items = []


def _is_weapon_item(item):
    if not item:
        return False
    return item.get("item_type") == "weapon" or item.get("equip_slot") == "weapon"


def _sync_equipment_state_from_inventory():
    global equipped_weapon_item_id, equipped_armor_item_id
    global PLAYER_WEAPON, PLAYER_ARMOR, PLAYER_AT_BONUS, PLAYER_DF_BONUS

    weapon_item = None
    armor_item = None
    for item in inventory_items:
        if weapon_item is None and item.get("id") == equipped_weapon_item_id:
            weapon_item = item
        if armor_item is None and item.get("id") == equipped_armor_item_id:
            armor_item = item
        if weapon_item and armor_item:
            break

    if weapon_item:
        PLAYER_WEAPON = weapon_item.get("name", "None")
        PLAYER_AT_BONUS = int(weapon_item.get("at_bonus", 0))
    else:
        equipped_weapon_item_id = None
        PLAYER_WEAPON = "None"
        PLAYER_AT_BONUS = 0

    if armor_item:
        PLAYER_ARMOR = armor_item.get("name", "None")
        PLAYER_DF_BONUS = int(armor_item.get("df_bonus", 0))
    else:
        equipped_armor_item_id = None
        PLAYER_DF_BONUS = 0


def _spawn_ground_drop_from_item(item, drop_map_id, px, py):
    global ground_weapon_drop_seq
    if not item:
        return False
    if not _is_weapon_item(item):
        return False
    # Randomly scatter drop around player feet instead of fixed side offset.
    safe_x = px
    safe_y = py
    found = False
    for _ in range(10):
        dx = _rand_range(-18, 18)
        dy = _rand_range(-10, 12)
        if -3 <= dx <= 3 and -3 <= dy <= 3:
            continue
        drop_x = _clamp(px + dx, PLAYER_R, world_w - PLAYER_R - 1)
        drop_y = _clamp(py + dy, PLAYER_R, world_h - PLAYER_R - 1)
        cand_x, cand_y = _nearest_walkable(drop_x, drop_y, max_radius=14)
        if not _collides(cand_x, cand_y, PLAYER_R):
            safe_x, safe_y = cand_x, cand_y
            found = True
            break
    if not found:
        fallback_x = _clamp(px + (14 if face_right else -14), PLAYER_R, world_w - PLAYER_R - 1)
        fallback_y = _clamp(py + 4, PLAYER_R, world_h - PLAYER_R - 1)
        safe_x, safe_y = _nearest_walkable(fallback_x, fallback_y, max_radius=20)
    drop = _inventory_clone_item(item)
    if not drop:
        return False
    ground_weapon_drop_seq += 1
    drop["drop_uid"] = "ground_drop_%d" % ground_weapon_drop_seq
    ground_weapon_drops.append(
        {
            "id": drop["drop_uid"],
            "map_id": drop_map_id,
            "x": safe_x,
            "y": safe_y,
            "item": drop,
        }
    )
    return True


def _drop_inventory_item_at(index):
    item = inventory_remove_at(index)
    if not item:
        return False
    if _is_weapon_item(item):
        _spawn_ground_drop_from_item(item, current_map_id, player_x, player_y)
    _sync_equipment_state_from_inventory()
    return True


def _equip_inventory_item(item):
    global equipped_weapon_item_id, equipped_armor_item_id
    if not item:
        return False
    slot = item.get("equip_slot")
    if slot == "weapon":
        equipped_weapon_item_id = item.get("id")
        _sync_equipment_state_from_inventory()
        return True
    if slot == "armor":
        equipped_armor_item_id = item.get("id")
        _sync_equipment_state_from_inventory()
        return True
    return False


def _inventory_clone_item(item):
    if not item:
        return None
    return {
        "id": item.get("id", "item"),
        "name": item.get("name", "Item"),
        "item_type": item.get("item_type", "consumable"),
        "equip_slot": item.get("equip_slot", "none"),
        "at_bonus": int(item.get("at_bonus", 0)),
        "df_bonus": int(item.get("df_bonus", 0)),
        "origin_pickup_id": item.get("origin_pickup_id"),
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
    item = inventory_items.pop(index)
    _sync_equipment_state_from_inventory()
    return item


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

def _init_display():
    global DISPLAY_INIT_DONE
    global battle_frame_x, battle_frame_y, battle_frame_x_max, battle_frame_y_max
    global battle_heart_init_x, battle_heart_init_y
    global battle_heart_min_x, battle_heart_max_x, battle_heart_min_y, battle_heart_max_y
    global battle_cmd_x0, battle_cmd_y, battle_cmd_w

    if not DISPLAY_INIT_DONE:
        lgfx.init()
        DISPLAY_INIT_DONE = True
    lgfx.set_rotation(ROTATION)
    if hasattr(lgfx, "tile_loader_mode"):
        try:
            print("tile_loader_mode:", lgfx.tile_loader_mode())
        except Exception as err:
            print("tile_loader_mode_error:", err)

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

asset_base = None
meta = None
tile = 0
map_w = 0
map_h = 0
world_w = 0
world_h = 0
runtime_endian = "little"
collision = None
player_x = 0
player_y = 0
player_sheet_enabled = False
player_sheet_err = None


def _tile_setup_with_fallback():
    global ACTIVE_VIEW_W, ACTIVE_VIEW_H

    # Fast path: try target fullscreen directly first.
    # Prefer PSRAM to keep internal heap headroom for slot/preload loader.
    gc.collect()
    if lgfx.tile_setup(tile, map_w, map_h, VIEW_W, VIEW_H, True):
        ACTIVE_VIEW_W, ACTIVE_VIEW_H = VIEW_W, VIEW_H
        print("tile_setup:", VIEW_W, VIEW_H, "psram:", True)
        return
    gc.collect()
    if lgfx.tile_setup(tile, map_w, map_h, VIEW_W, VIEW_H, False):
        ACTIVE_VIEW_W, ACTIVE_VIEW_H = VIEW_W, VIEW_H
        print("tile_setup:", VIEW_W, VIEW_H, "psram:", False)
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

    # Fullscreen is the intended mode. Retry it first, preferring PSRAM so
    # slot-loader allocations are less likely to fail on large maps.
    if VIEW_W <= world_w and VIEW_H <= world_h:
        if _try_setup(VIEW_W, VIEW_H, (True, False), FULL_VIEW_SETUP_RETRIES):
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
        if _try_setup(vw, vh, (True, False), 1):
            return
    raise RuntimeError("TILE_SETUP_FAIL")


def _render_scene(scroll_x, scroll_y, player_x, player_y, force_full):
    if USE_TILE_RENDER_PLAYER_COMPOSE and hasattr(lgfx, "tile_render_player"):
        lgfx.tile_render_player(scroll_x, scroll_y, player_x - scroll_x, player_y - scroll_y, PLAYER_COLOR, PLAYER_R, force_full)
    else:
        lgfx.tile_render(scroll_x, scroll_y, force_full)
        lgfx.draw_player(player_x - scroll_x, player_y - scroll_y, PLAYER_COLOR, PLAYER_R)

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


battle_frame_x = 0
battle_frame_y = 0
battle_frame_x_max = 0
battle_frame_y_max = 0
battle_heart_init_x = 0
battle_heart_init_y = 0
battle_heart_min_x = 0
battle_heart_max_x = 0
battle_heart_min_y = 0
battle_heart_max_y = 0
battle_cmd_x0 = 0
battle_cmd_y = 0
battle_cmd_w = 0

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


def _draw_boot_time_card(text):
    lgfx.clear()
    digit_w = 16
    digit_h = 28
    seg_th = 3
    gap = 4
    colon_w = 6
    color = BATTLE_COLOR_WHITE

    segments_map = {
        "0": "abcedf",
        "1": "bc",
        "2": "abged",
        "3": "abgcd",
        "4": "fgbc",
        "5": "afgcd",
        "6": "afgecd",
        "7": "abc",
        "8": "abcdefg",
        "9": "abfgcd",
    }

    def _fill(x, y, w, h):
        if w <= 0 or h <= 0:
            return
        yy = y
        y_end = y + h
        while yy < y_end:
            lgfx.draw_rect(x, yy, w, 1, color)
            yy += 1

    def _draw_digit(ch, x, y):
        segs = segments_map.get(ch)
        if not segs:
            return
        mid_y = y + (digit_h // 2) - (seg_th // 2)
        half_h = digit_h // 2
        if "a" in segs:
            _fill(x + seg_th, y, digit_w - (seg_th * 2), seg_th)
        if "d" in segs:
            _fill(x + seg_th, y + digit_h - seg_th, digit_w - (seg_th * 2), seg_th)
        if "g" in segs:
            _fill(x + seg_th, mid_y, digit_w - (seg_th * 2), seg_th)
        if "f" in segs:
            _fill(x, y + seg_th, seg_th, half_h - seg_th)
        if "e" in segs:
            _fill(x, y + half_h, seg_th, half_h - seg_th)
        if "b" in segs:
            _fill(x + digit_w - seg_th, y + seg_th, seg_th, half_h - seg_th)
        if "c" in segs:
            _fill(x + digit_w - seg_th, y + half_h, seg_th, half_h - seg_th)

    def _draw_colon(x, y):
        dot = seg_th + 1
        top_y = y + (digit_h // 3) - (dot // 2)
        bot_y = y + ((digit_h * 2) // 3) - (dot // 2)
        _fill(x + 1, top_y, dot, dot)
        _fill(x + 1, bot_y, dot, dot)

    total_w = 0
    for i, ch in enumerate(text):
        if ch == ":":
            total_w += colon_w
        else:
            total_w += digit_w
        if i != len(text) - 1:
            total_w += gap
    x = (VIEW_W - total_w) // 2
    y = (VIEW_H - digit_h) // 2
    if x < 0:
        x = 0
    if y < 0:
        y = 0

    for i, ch in enumerate(text):
        if ch == ":":
            _draw_colon(x, y)
            x += colon_w
        else:
            _draw_digit(ch, x, y)
            x += digit_w
        if i != len(text) - 1:
            x += gap


def _draw_boot_comic_frame(path):
    lgfx.clear()
    if not path or not hasattr(lgfx, "draw_png_file"):
        return
    try:
        if not _path_exists(path):
            return
        lgfx.draw_png_file(path, 0, 0, VIEW_W, VIEW_H)
    except Exception:
        pass


def _boot_phase_sd_ready():
    global SD_READY
    if ENABLE_SD_MOUNT:
        _try_mount_sd()
    else:
        SD_READY = False
        print("sd_mounted:", SD_READY, "(disabled)")


def _boot_phase_meta_spawn():
    global asset_base, meta, tile, map_w, map_h, world_w, world_h
    global player_x, player_y

    asset_base, meta = _find_asset_base(MAP1_ASSET_BASES)
    print("asset:", asset_base)
    if asset_base == MAP_REGISTRY[MAP1_ID]["asset_base"]:
        _print_asset_files(asset_base, meta)
    if hasattr(lgfx, "set_swap_bytes"):
        lgfx.set_swap_bytes(meta.get("endian", "little") == "little")
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


def _boot_phase_tile_and_player():
    global player_sheet_enabled, player_sheet_err, map6_boss_sheet_loaded
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

    map6_boss_sheet_loaded = _load_map6_boss_sheet()

    print("view:", ACTIVE_VIEW_W, ACTIVE_VIEW_H)


def _boot_phase_tile_data():
    global runtime_endian
    _resident_boot_activate_map(MAP1_ID)
    runtime_endian = "little"
    if hasattr(lgfx, "set_swap_bytes"):
        lgfx.set_swap_bytes(runtime_endian == "little")


def _boot_phase_collision():
    if collision is None:
        raise RuntimeError("COLLISION_REQUIRED")
    blocked_tiles = 0
    for v in collision:
        if v:
            blocked_tiles += 1
    print("collision_tiles:", blocked_tiles, "/", map_w * map_h)
    if blocked_tiles == 0 and (not resident_slots[resident_active_slot_id].get("fallback_all_walkable")):
        raise RuntimeError("COLLISION_EMPTY")


def _boot_phase_finalize_startup():
    global player_x, player_y
    global battle_frame_x, battle_frame_y, battle_frame_x_max, battle_frame_y_max
    global battle_heart_init_x, battle_heart_init_y
    global battle_heart_min_x, battle_heart_max_x, battle_heart_min_y, battle_heart_max_y
    global battle_cmd_x0, battle_cmd_y, battle_cmd_w

    _collision_selftest()

    # Keep startup robust when map metadata spawn lands inside a blocked tile.
    safe_start_x, safe_start_y = _nearest_walkable(player_x, player_y)
    if safe_start_x != player_x or safe_start_y != player_y:
        print("startup_spawn_adjusted:", player_x, player_y, "->", safe_start_x, safe_start_y)
    player_x, player_y = safe_start_x, safe_start_y

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


def _fnv1a32_text(text):
    h = 2166136261
    for b in text.encode():
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _resident_map_token(map_id):
    return int(map_id) & 0xFFFFFFFF


def _resident_tileset_token(config, tile_base):
    tileset_key = config.get("tileset_id")
    if tileset_key is None:
        tileset_key = tile_base + "/tileset.bin"
    return _fnv1a32_text(str(tileset_key))


def _resident_slot_state_name(state):
    if state == SLOT_STATE_EMPTY:
        return "EMPTY"
    if state == SLOT_STATE_LOADING:
        return "LOADING"
    if state == SLOT_STATE_READY:
        return "READY"
    if state == SLOT_STATE_FAILED:
        return "FAILED"
    return "?"


def _resident_slot_stage_name(stage):
    if stage == SLOT_STAGE_NONE:
        return "NONE"
    if stage == SLOT_STAGE_VALIDATE:
        return "VALIDATE"
    if stage == SLOT_STAGE_ACQUIRE_TILESET:
        return "ACQUIRE_TILESET"
    if stage == SLOT_STAGE_WAIT_TILESET:
        return "WAIT_TILESET"
    if stage == SLOT_STAGE_LOAD_TILESET:
        return "LOAD_TILESET"
    if stage == SLOT_STAGE_LOAD_TILEMAP:
        return "LOAD_TILEMAP"
    if stage == SLOT_STAGE_READY:
        return "READY"
    return "?"


def _resident_role_name(role):
    if role == SLOT_ROLE_BACK:
        return "back"
    if role == SLOT_ROLE_ACTIVE:
        return "active"
    if role == SLOT_ROLE_AHEAD:
        return "ahead"
    return "none"


def _resident_slot_info(slot_id):
    if not hasattr(lgfx, "slot_info"):
        return None
    info = lgfx.slot_info(slot_id)
    if not info or len(info) < 10:
        return None
    return {
        "role": info[0],
        "state": info[1],
        "map_token": info[2],
        "tileset_token": info[3],
        "load_stage": info[4],
        "loaded_bytes": info[5],
        "total_bytes": info[6],
        "ref_count": info[7],
        "waiter_count": info[8],
        "is_active": bool(info[9]),
    }


def _resident_sync_roles():
    resident_slots[resident_back_slot_id]["role"] = SLOT_ROLE_BACK
    resident_slots[resident_active_slot_id]["role"] = SLOT_ROLE_ACTIVE
    resident_slots[resident_ahead_slot_id]["role"] = SLOT_ROLE_AHEAD
    if hasattr(lgfx, "slot_set_role"):
        lgfx.slot_set_role(resident_back_slot_id, SLOT_ROLE_BACK)
        lgfx.slot_set_role(resident_active_slot_id, SLOT_ROLE_ACTIVE)
        lgfx.slot_set_role(resident_ahead_slot_id, SLOT_ROLE_AHEAD)


def _resident_clear_slot_record(slot_id):
    role = resident_slots[slot_id]["role"]
    resident_slots[slot_id] = {
        "role": role,
        "map_id": None,
        "map_token": 0,
        "tileset_token": 0,
        "asset_base": None,
        "tile_base": None,
        "meta": None,
        "collision": None,
        "spawn": None,
        "fallback_all_walkable": False,
    }


def _resident_release_slot(slot_id, reason=None):
    global preload_last_release_ms, preload_release_due_ms
    global perf_preload_release_count
    if slot_id == resident_active_slot_id:
        return False
    info = _resident_slot_info(slot_id)
    if info is not None and info["state"] == SLOT_STATE_LOADING and hasattr(lgfx, "display_wait_idle"):
        lgfx.display_wait_idle()
    ok = True
    if info is not None and info["state"] == SLOT_STATE_LOADING:
        cancel_ok = True
        if hasattr(lgfx, "slot_cancel_load"):
            cancel_ok = bool(lgfx.slot_cancel_load(slot_id))
        release_ok = True
        if hasattr(lgfx, "slot_release"):
            release_ok = bool(lgfx.slot_release(slot_id))
        ok = bool(cancel_ok and release_ok)
    elif hasattr(lgfx, "slot_release"):
        ok = bool(lgfx.slot_release(slot_id))
    _resident_clear_slot_record(slot_id)
    _resident_sync_roles()
    if reason:
        print("preload_release:", reason)
    preload_last_release_ms = time.ticks_ms()
    preload_release_due_ms = 0
    perf_preload_release_count += 1
    return ok


def _resident_apply_slot_globals(slot_id):
    global asset_base, meta, tile, map_w, map_h, world_w, world_h
    global collision, runtime_endian
    slot = resident_slots[slot_id]
    meta = slot["meta"]
    asset_base = slot["asset_base"]
    collision = slot["collision"]
    tile = meta["tile_size"]
    map_w = meta["map_w"]
    map_h = meta["map_h"]
    world_w = map_w * tile
    world_h = map_h * tile
    runtime_endian = "little"


def _resident_log_slots(prefix):
    for slot_id in RESIDENT_SLOT_IDS:
        info = _resident_slot_info(slot_id)
        record = resident_slots[slot_id]
        if info is None:
            print(prefix, "slot", slot_id, "info:missing")
            continue
        print(
            prefix,
            "slot", slot_id,
            _resident_role_name(record["role"]),
            "map", record["map_id"],
            "state", _resident_slot_state_name(info["state"]),
            "stage", _resident_slot_stage_name(info["load_stage"]),
            "loaded", info["loaded_bytes"], "/", info["total_bytes"],
            "ref", info["ref_count"],
            "wait", info["waiter_count"],
            "active", info["is_active"],
        )


def _resident_resolve_map_record(target_map_id, spawn=None):
    config = MAP_REGISTRY.get(target_map_id)
    if not config:
        raise RuntimeError("TARGET_MAP_UNKNOWN")
    base, next_meta = _find_asset_base(config["asset_bases"])
    if next_meta.get("endian", "little") != "little":
        raise RuntimeError("TILE_ENDIAN_UNSUPPORTED")
    fallback_all_walkable = bool(config.get("fallback_all_walkable", False))
    map_w2 = next_meta["map_w"]
    map_h2 = next_meta["map_h"]
    if fallback_all_walkable:
        collision_data = bytearray(map_w2 * map_h2)
    else:
        collision_data, collision_err = _load_collision(next_meta, base, map_w2, map_h2)
        if collision_data is None:
            raise RuntimeError(collision_err if collision_err else "COLLISION_REQUIRED")
    return {
        "map_id": target_map_id,
        "map_token": _resident_map_token(target_map_id),
        "tileset_token": _resident_tileset_token(config, base),
        "asset_base": base,
        "tile_base": base,
        "meta": next_meta,
        "collision": collision_data,
        "spawn": spawn,
        "fallback_all_walkable": fallback_all_walkable,
    }


def _resident_slot_has_target(slot_id, target_map_id):
    record = resident_slots[slot_id]
    if record["map_id"] != target_map_id:
        return False
    info = _resident_slot_info(slot_id)
    if info is None or info["state"] not in (SLOT_STATE_LOADING, SLOT_STATE_READY):
        return False
    if not hasattr(lgfx, "slot_has_map"):
        return False
    return bool(lgfx.slot_has_map(slot_id, record["map_token"]))


def _resident_start_slot_load(slot_id, record, sync_load):
    _resident_release_slot(slot_id, "replace_slot")
    resident_slots[slot_id].update(record)
    resident_slots[slot_id]["role"] = resident_slots[slot_id]["role"]
    args = (
        slot_id,
        record["map_token"],
        record["tileset_token"],
        record["tile_base"] + "/tileset.bin",
        record["tile_base"] + "/tilemap.bin",
        record["meta"]["tile_size"],
        record["meta"]["map_w"],
        record["meta"]["map_h"],
    )
    if sync_load:
        ok = lgfx.slot_load_files(*args)
    else:
        ok = lgfx.slot_begin_load_files(*args)
        if not ok:
            # Fallback to synchronous load when async begin fails (slot may
            # still be settling after a cancel/release on some firmware builds).
            if hasattr(lgfx, "display_wait_idle"):
                lgfx.display_wait_idle()
            ok = lgfx.slot_load_files(*args)
    if not ok:
        state = _resident_slot_info(slot_id)
        print("resident_slot_load_fail:", slot_id, record["map_id"], state)
        resident_slots[slot_id]["map_id"] = record["map_id"]
        return False
    return True


def _resident_finish_slot_sync(slot_id):
    info = _resident_slot_info(slot_id)
    if info is None:
        return False
    if info["state"] == SLOT_STATE_READY:
        return True
    if info["state"] != SLOT_STATE_LOADING:
        return False
    while True:
        pumped = lgfx.slot_pump_load(slot_id, PRELOAD_BUDGET_BYTES * 16)
        if pumped < 0:
            return False
        info = _resident_slot_info(slot_id)
        if info is None:
            return False
        if info["state"] == SLOT_STATE_READY:
            return True
        if info["state"] == SLOT_STATE_FAILED:
            return False
        if pumped == 0:
            time.sleep_ms(1)


def _resident_prepare_active_slot(slot_id):
    _resident_apply_slot_globals(slot_id)
    _tile_setup_with_fallback()
    if hasattr(lgfx, "display_wait_idle"):
        lgfx.display_wait_idle()
    if not lgfx.slot_select(slot_id, True):
        raise RuntimeError("slot_select_fail")


def _resident_restore_active_slot(slot_id):
    _resident_prepare_active_slot(slot_id)


def _resident_boot_activate_map(target_map_id):
    global resident_back_slot_id, resident_active_slot_id, resident_ahead_slot_id
    resident_back_slot_id = RESIDENT_BACK_SLOT_ID
    resident_active_slot_id = RESIDENT_ACTIVE_SLOT_ID
    resident_ahead_slot_id = RESIDENT_AHEAD_SLOT_ID
    for slot_id in RESIDENT_SLOT_IDS:
        if hasattr(lgfx, "slot_release"):
            try:
                lgfx.slot_release(slot_id)
            except Exception:
                pass
        _resident_clear_slot_record(slot_id)
    _resident_sync_roles()
    record = _resident_resolve_map_record(target_map_id)
    if not _resident_start_slot_load(resident_active_slot_id, record, True):
        raise RuntimeError("RESIDENT_BOOT_LOAD_FAIL")
    resident_slots[resident_active_slot_id].update(record)
    _resident_prepare_active_slot(resident_active_slot_id)
    _resident_log_slots("boot_slot")


def _play_boot_comic_intro():
    phases = (
        _boot_phase_sd_ready,
        _boot_phase_meta_spawn,
        _boot_phase_tile_and_player,
        _boot_phase_tile_data,
        _boot_phase_collision,
        _boot_phase_finalize_startup,
    )

    def _wait_slot(ms):
        deadline = time.ticks_add(time.ticks_ms(), ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            time.sleep_ms(10)

    for i in range(len(BOOT_COMIC_TIME_LABELS)):
        _draw_boot_time_card(BOOT_COMIC_TIME_LABELS[i])
        _wait_slot(BOOT_TIME_CARD_MS)
        _draw_boot_comic_frame(BOOT_COMIC_PATHS[i])
        # Keep the first 5 comics strictly fixed.
        if i < (len(BOOT_COMIC_TIME_LABELS) - 1):
            _wait_slot(BOOT_COMIC_FRAME_MS)
            continue

        # Run all startup phases during the last comic only.
        last_deadline = time.ticks_add(time.ticks_ms(), BOOT_COMIC_FRAME_MS)
        for phase_fn in phases:
            phase_fn()
        while time.ticks_diff(last_deadline, time.ticks_ms()) > 0:
            time.sleep_ms(10)

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
        collision_data = None
        collision_err = None
        if fallback_all_walkable:
            # For maps explicitly marked fallback-all-walkable, skip collision load.
            # This prevents accidentally inheriting other map collision data.
            pass
        else:
            collision_data = preloaded_collision
            if collision_data is not None and len(collision_data) != map_w * map_h:
                raise RuntimeError("PRELOAD_COLLISION_SIZE_MISMATCH")
            if collision_data is None:
                collision_data, collision_err = _load_collision(meta, asset_base, map_w, map_h)
    except Exception as err:
        raise RuntimeError("collision_load:%s" % err)
    phase["collision_load_ms"] = time.ticks_diff(time.ticks_ms(), t0)

    if collision_data is None:
        if not fallback_all_walkable:
            raise RuntimeError("COLLISION_REQUIRED")
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
    global move_carry_x, move_carry_y, prev_input_x, prev_input_y
    global preload_suspend_until_ms, gc_suspend_until_ms, gc_pending
    global resident_back_slot_id, resident_active_slot_id, resident_ahead_slot_id
    global resident_transition_active
    global preload_zone_target_map_id, preload_zone_enter_ms

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
    prev_back_slot_id = resident_back_slot_id
    prev_active_slot_id = resident_active_slot_id
    prev_ahead_slot_id = resident_ahead_slot_id

    def _tile_last_error_code():
        if hasattr(lgfx, "tile_last_error"):
            try:
                return lgfx.tile_last_error()
            except Exception:
                return None
        return None

    target_slot_id = None
    if _resident_slot_has_target(resident_back_slot_id, target_map_id):
        target_slot_id = resident_back_slot_id
    elif _resident_slot_has_target(resident_ahead_slot_id, target_map_id):
        target_slot_id = resident_ahead_slot_id
    else:
        fail_stage = "resolve_base"
        t0 = time.ticks_ms()
        try:
            record = _resident_resolve_map_record(target_map_id, (spawn_x, spawn_y) if spawn_x is not None and spawn_y is not None else None)
        except Exception as err:
            print("switch_map_skip_target:", target_map_id, err)
            print("switch_map_fail_stage:resolve_base")
            phase["resolve_base_ms"] = time.ticks_diff(time.ticks_ms(), t0)
            _print_switch_timings()
            teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
            return False
        phase["resolve_base_ms"] = time.ticks_diff(time.ticks_ms(), t0)
        target_slot_id = resident_ahead_slot_id
        # Reduce heap fragmentation before slot loader allocates its tile cache.
        gc.collect()
        load_started = _resident_start_slot_load(target_slot_id, record, False)
        if not load_started:
            last_err = _tile_last_error_code()
            if last_err == 8:
                # Loader cache allocation failed. Free back slot payload and
                # retry once before bailing out.
                gc.collect()
                _resident_release_slot(resident_back_slot_id, "switch_retry_release_back")
                gc.collect()
                load_started = _resident_start_slot_load(target_slot_id, record, False)
                if load_started:
                    last_err = 0
            if last_err:
                print("switch_map_tile_last_error:", last_err)
        if not load_started:
            if last_err == 8:
                if target_map_id == MAP8_ID:
                    # Slot loader can fail on very large maps even when PSRAM is
                    # available. Use the direct loader as a targeted fallback for
                    # Map8 instead of aborting the portal transition.
                    if _switch_map_direct_fallback(target_map_id, record, spawn_x, spawn_y):
                        return True
                try:
                    tile_bytes = record["meta"]["tile_size"] * record["meta"]["tile_size"] * 2
                    print(
                        "switch_map_diag_target:",
                        target_map_id,
                        "map_w", record["meta"]["map_w"],
                        "map_h", record["meta"]["map_h"],
                        "tileset_count", (os.stat(record["tile_base"] + "/tileset.bin")[6] // tile_bytes),
                    )
                except Exception:
                    pass
            print("switch_map_fail_stage:slot_begin")
            _print_switch_timings()
            teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
            return False

    target_record = resident_slots[target_slot_id]
    if spawn_x is None and target_record.get("spawn") and len(target_record["spawn"]) >= 2:
        spawn_x = target_record["spawn"][0]
    if spawn_y is None and target_record.get("spawn") and len(target_record["spawn"]) >= 2:
        spawn_y = target_record["spawn"][1]

    collision = None
    meta = None
    asset_base = None
    gc.collect()
    resident_transition_active = True

    try:
        fail_stage = "tile_load"
        t0 = time.ticks_ms()
        target_info = _resident_slot_info(target_slot_id)
        if target_info is None:
            raise RuntimeError("slot_info_missing")
        if target_info["state"] != SLOT_STATE_READY:
            if not _resident_finish_slot_sync(target_slot_id):
                raise RuntimeError("resident_load_failed")
        phase["tile_load_ms"] = time.ticks_diff(time.ticks_ms(), t0)

        fail_stage = "map_context"
        _resident_apply_slot_globals(target_slot_id)
        phase["map_json_ms"] = 0
        phase["collision_load_ms"] = 0

        fail_stage = "tile_setup"
        t0 = time.ticks_ms()
        _tile_setup_with_fallback()
        phase["tile_setup_ms"] = time.ticks_diff(time.ticks_ms(), t0)

        fail_stage = "slot_select"
        if hasattr(lgfx, "display_wait_idle"):
            lgfx.display_wait_idle()
        if not lgfx.slot_select(target_slot_id, True):
            raise RuntimeError("slot_select_failed")
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
        resident_back_slot_id = prev_back_slot_id
        resident_active_slot_id = prev_active_slot_id
        resident_ahead_slot_id = prev_ahead_slot_id
        _resident_sync_roles()
        try:
            _resident_restore_active_slot(prev_active_slot_id)
        except Exception as restore_err:
            print("switch_map_restore_slot_fail:", restore_err)
        print("switch_map_restore:", err)
        print("switch_map_fail_stage:%s" % (fail_stage if fail_stage else "unknown"))
        _print_switch_timings()
        teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
        resident_transition_active = False
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
    # Drop per-axis carry across map boundaries so map-specific speed never leaks.
    move_carry_x = 0
    move_carry_y = 0
    prev_input_x = 0
    prev_input_y = 0

    leaf_zone_prev_inside = False
    explore_overlay_dirty = False
    lamp_dialog_until_ms = 0
    # Keep startup-only intro effect; do not re-enable it on map switches.
    explore_force_full_redraw = True
    teleport_cooldown_frames = TELEPORT_COOLDOWN_FRAMES
    phase["spawn_finalize_ms"] = time.ticks_diff(time.ticks_ms(), t0)
    current_map_id = target_map_id
    _encounter_on_map_enter(current_map_id)

    if target_slot_id == prev_back_slot_id:
        resident_active_slot_id = prev_back_slot_id
        resident_back_slot_id = prev_active_slot_id
    else:
        resident_active_slot_id = target_slot_id
        resident_back_slot_id = prev_active_slot_id
    for slot_id in RESIDENT_SLOT_IDS:
        if slot_id not in (resident_active_slot_id, resident_back_slot_id):
            resident_ahead_slot_id = slot_id
            break
    _resident_sync_roles()
    _resident_release_slot(resident_ahead_slot_id, "switch_recycle")
    preload_zone_target_map_id = None
    preload_zone_enter_ms = 0

    now = time.ticks_ms()
    preload_suspend_until_ms = time.ticks_add(now, PRELOAD_POST_SWITCH_PAUSE_MS)
    gc_suspend_until_ms = time.ticks_add(now, GC_POST_SWITCH_PAUSE_MS)
    _print_switch_timings()
    _resident_log_slots("switch_slot")
    if GC_DEFER_ENABLE:
        gc_pending = True
    else:
        gc.collect()
    resident_transition_active = False
    return True


adc_x = None
adc_y = None
interact_sw = None
btn_fight = None
btn_act = None
btn_item = None
btn_mercy = None
button_last_edge_ms = {}


def _init_runtime_state():
    global adc_x, adc_y, interact_sw, btn_fight, btn_act, btn_item, btn_mercy, cx
    global cy, axis_max, frame, t0, scroll_x, scroll_y, cam_margin_x, cam_margin_y
    global prev_scroll_x, prev_scroll_y, prev_player_x, prev_player_y, x_dir, y_dir_raw, anim_row, anim_col
    global anim_last_ms, face_right, move_carry_x, move_carry_y, prev_input_x, prev_input_y, prev_loop_ms, last_input_active_ms
    global anim_x_dir, anim_y_dir, explore_moved, explore_scrolled, explore_anim_changed, explore_force_full_redraw, mode, title_menu_index
    global title_nav_prev_dir, title_nav_next_ms, title_notice_until_ms, title_notice_text, title_dirty, title_full_redraw, title_cover_drew_png, encounter_cooldown_frames
    global act_dialog_until_ms, fight_heart_x, fight_heart_y, battle_prev_heart_x, battle_prev_heart_y, battle_menu_dirty, battle_fight_dirty, battle_dialog_visible
    global battle_dialog_mode, battle_dialog_started_ms, battle_dialog_png_info, battle_dialog_text, act_menu_active, act_choice_index, act_sequence_step, act_nav_prev_dir
    global act_menu_slot_cache, act_prev_selected_index, act_selection_dirty, item_menu_active, item_choice_index, item_nav_prev_dir, item_menu_slot_cache, item_prev_selected_index
    global item_selection_dirty, item_view_offset, menu_frame_x_used, menu_frame_w_used, menu_cmd_y_used, battle_heart_needs_sprite_refresh, fight_return_deadline_ms, player_hp
    global enemy_hp, bullets, next_bullet_spawn_ms, damage_invuln_until_ms, battle_bullets_dirty, battle_prev_bullet_positions, battle_status_dirty, attack_started_ms
    global attack_cursor_x, attack_cursor_dir, attack_locked, battle_attack_dirty, attack_prev_cursor_draw_x, mercy_exit_pending, battle_menu_full_clear_pending, battle_menu_static_ready
    global battle_menu_static_frame_x, battle_menu_static_frame_y, battle_menu_static_frame_w, battle_menu_enemy_bottom_used, battle_menu_enemy_x, battle_menu_enemy_y, battle_menu_enemy_w, battle_menu_enemy_h
    global battle_menu_prev_dialog_active, battle_menu_prev_dialog_x, battle_menu_prev_dialog_y, battle_menu_prev_dialog_w, battle_menu_prev_dialog_h, map1_story_active, map1_story_stage, map1_story_line_index
    global map1_story_next_ms, map1_story_enemy_angry, map1_enemy_anchor_mode, map1_enemy_slide_start_ms, map1_story_phase2_center_x, map1_story_phase2_center_y
    global map1_story_phase2_event, map1_story_phase2_event_started_ms, map1_story_phase2_freeze_until_ms
    global map1_story_fire_x, map1_story_fire_y, map1_story_fire_start_x, map1_story_fire_start_y, map1_story_fire_target_x, map1_story_fire_target_y
    global map1_story_flowey_hidden, map1_story_toriel_visible, map1_story_toriel_x, map1_story_toriel_start_x, map1_story_toriel_target_x
    global map1_story_fire_prev_x, map1_story_fire_prev_y, map1_story_fire_prev_valid
    global map1_story_toriel_prev_x, map1_story_toriel_prev_y, map1_story_toriel_prev_valid, map1_story_prev_flowey_visible
    global _rng_state, interact_sw_prev
    global btn_fight_prev, btn_act_prev, btn_item_prev, btn_mercy_prev, leaf_zone_prev_inside, map1_opening_battle_timer_started, map1_opening_battle_due_ms, map1_opening_battle_done
    global lamp_dialog_until_ms, explore_overlay_dirty, current_map_id, teleport_cooldown_frames, inv_choice_index, inv_nav_prev_dir, inv_drop_active, inv_drop_choice_index
    global inv_drop_choice_count, inv_drop_nav_prev_dir, inv_screen_dirty, INV_TAB_ITEM, INV_TAB_STAT, INV_FOCUS_LEFT, INV_FOCUS_RIGHT, inv_tab_index
    global inv_tab_active, inv_tab_nav_prev_dir, inv_focus_side, inv_focus_nav_prev_dir, weapon_pickup_dialog_active, weapon_pickup_choice_index, weapon_pickup_nav_prev_dir, weapon_pickup_target
    global weapon_pickup_dialog_dirty, spawn_intro_cleared_once, spawn_intro_active, spawn_intro_overlay_path, spawn_intro_needs_redraw, inventory_portrait_path, title_cover_path, title_ui_start_path
    global title_ui_continue_path, button_last_edge_ms
    global portal_transition_active, portal_transition_started_ms, portal_transition_stage
    global portal_transition_source_map_id, portal_transition_target_map_id, portal_transition_target_spawn
    global portal_transition_center_screen_x, portal_transition_center_screen_y
    global portal_transition_shrink_ms, portal_transition_black_ms, portal_transition_portal_ref, portal_transition_last_switch_try_ms
    global portal_transition_switch_fail_count
    global portal_transition_rearm_required, portal_transition_rearm_map_id, portal_transition_rearm_portal_ref
    global map6_boss_defeated, map6_boss_battle_active, map6_boss_anim_seq_index, map6_boss_anim_last_ms
    adc_x = ADC(Pin(JOY_X_PIN))
    adc_y = ADC(Pin(JOY_Y_PIN))
    adc_x.atten(ADC.ATTN_11DB)
    adc_y.atten(ADC.ATTN_11DB)
    interact_sw = Pin(ENCOUNTER_SW_PIN, Pin.IN, Pin.PULL_UP)
    btn_fight = Pin(BTN_FIGHT_PIN, Pin.IN, Pin.PULL_UP)
    btn_act = Pin(BTN_ACT_PIN, Pin.IN, Pin.PULL_UP)
    btn_item = Pin(BTN_ITEM_PIN, Pin.IN, Pin.PULL_UP)
    btn_mercy = Pin(BTN_MERCY_PIN, Pin.IN, Pin.PULL_UP)
    button_last_edge_ms = {}
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
    mode = MODE_TITLE_MENU
    title_menu_index = 0
    title_nav_prev_dir = 0
    title_nav_next_ms = 0
    title_notice_until_ms = 0
    title_notice_text = None
    title_dirty = True
    title_full_redraw = True
    title_cover_drew_png = False
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
    enemy_hp = ENEMY_HP_MAX
    bullets = []
    next_bullet_spawn_ms = 0
    damage_invuln_until_ms = 0
    battle_bullets_dirty = False
    battle_prev_bullet_positions = []
    battle_status_dirty = True
    attack_started_ms = 0
    attack_cursor_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_BAR_W) // 2)
    attack_cursor_dir = 1
    attack_locked = False
    battle_attack_dirty = True
    attack_prev_cursor_draw_x = -9999
    mercy_exit_pending = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    battle_menu_static_frame_x = battle_frame_x
    battle_menu_static_frame_y = battle_frame_y
    battle_menu_static_frame_w = BATTLE_FRAME_W
    battle_menu_enemy_bottom_used = battle_frame_y + 88
    battle_menu_enemy_x = battle_frame_x + ((BATTLE_FRAME_W - ENEMY_SPRITE_W) // 2)
    battle_menu_enemy_y = battle_frame_y + 16
    battle_menu_enemy_w = ENEMY_SPRITE_W
    battle_menu_enemy_h = ENEMY_SPRITE_H
    battle_menu_prev_dialog_active = False
    battle_menu_prev_dialog_x = 0
    battle_menu_prev_dialog_y = 0
    battle_menu_prev_dialog_w = 0
    battle_menu_prev_dialog_h = 0
    map1_story_active = False
    map1_story_stage = MAP1_STORY_STAGE_NONE
    map1_story_line_index = -1
    map1_story_next_ms = 0
    map1_story_enemy_angry = False
    map1_enemy_anchor_mode = MAP1_ENEMY_ANCHOR_CENTER
    map1_enemy_slide_start_ms = 0
    map1_story_phase2_center_x = 0
    map1_story_phase2_center_y = 0
    map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_NONE
    map1_story_phase2_event_started_ms = 0
    map1_story_phase2_freeze_until_ms = 0
    map1_story_fire_x = 0
    map1_story_fire_y = 0
    map1_story_fire_start_x = 0
    map1_story_fire_start_y = 0
    map1_story_fire_target_x = 0
    map1_story_fire_target_y = 0
    map1_story_flowey_hidden = False
    map1_story_toriel_visible = False
    map1_story_toriel_x = 0
    map1_story_toriel_start_x = 0
    map1_story_toriel_target_x = 0
    map1_story_fire_prev_x = 0
    map1_story_fire_prev_y = 0
    map1_story_fire_prev_valid = False
    map1_story_toriel_prev_x = 0
    map1_story_toriel_prev_y = 0
    map1_story_toriel_prev_valid = False
    map1_story_prev_flowey_visible = True
    _rng_state = (time.ticks_ms() | 1) & 0x7FFFFFFF
    interact_sw_prev = interact_sw.value()
    btn_fight_prev = btn_fight.value()
    btn_act_prev = btn_act.value()
    btn_item_prev = btn_item.value()
    btn_mercy_prev = btn_mercy.value()
    leaf_zone_prev_inside = False
    map1_opening_battle_timer_started = False
    map1_opening_battle_due_ms = 0
    map1_opening_battle_done = False
    lamp_dialog_until_ms = 0
    explore_overlay_dirty = False
    current_map_id = MAP1_ID
    teleport_cooldown_frames = 0
    inv_choice_index = 0
    inv_nav_prev_dir = 0
    inv_drop_active = False
    inv_drop_choice_index = 0
    inv_drop_choice_count = 2
    inv_drop_nav_prev_dir = 0
    inv_screen_dirty = True
    INV_TAB_ITEM = 0
    INV_TAB_STAT = 1
    INV_FOCUS_LEFT = 0
    INV_FOCUS_RIGHT = 1
    inv_tab_index = INV_TAB_ITEM
    inv_tab_active = INV_TAB_ITEM
    inv_tab_nav_prev_dir = 0
    inv_focus_side = INV_FOCUS_LEFT
    inv_focus_nav_prev_dir = 0
    weapon_pickup_dialog_active = False
    weapon_pickup_choice_index = 0
    weapon_pickup_nav_prev_dir = 0
    weapon_pickup_target = None
    weapon_pickup_dialog_dirty = False
    spawn_intro_cleared_once = False
    spawn_intro_active = bool(ENABLE_SPAWN_INTRO and (current_map_id == MAP1_ID))
    spawn_intro_overlay_path = _resolve_first_existing_path(SPAWN_OVERLAY_PATHS) if spawn_intro_active else None
    spawn_intro_needs_redraw = spawn_intro_active
    portal_transition_active = False
    portal_transition_started_ms = 0
    portal_transition_stage = "none"
    portal_transition_source_map_id = 0
    portal_transition_target_map_id = 0
    portal_transition_target_spawn = None
    portal_transition_center_screen_x = 0
    portal_transition_center_screen_y = 0
    portal_transition_shrink_ms = PORTAL_TRANSITION_DEFAULT_SHRINK_MS
    portal_transition_black_ms = PORTAL_TRANSITION_DEFAULT_BLACK_MS
    portal_transition_portal_ref = None
    portal_transition_last_switch_try_ms = 0
    portal_transition_switch_fail_count = 0
    portal_transition_rearm_required = False
    portal_transition_rearm_map_id = 0
    portal_transition_rearm_portal_ref = None
    map6_boss_defeated = False
    map6_boss_battle_active = False
    map6_boss_anim_seq_index = 0
    map6_boss_anim_last_ms = time.ticks_ms()
    inventory_portrait_path = _resolve_first_existing_path(INVENTORY_PORTRAIT_PATHS)
    title_cover_path = _resolve_first_existing_path(TITLE_COVER_PATHS)
    title_ui_start_path = _resolve_first_existing_path(TITLE_UI_START_PATHS)
    title_ui_continue_path = _resolve_first_existing_path(TITLE_UI_CONTINUE_PATHS)

    if player_sheet_enabled:
        lgfx.player_frame_set(anim_row * 3 + anim_col)
        if hasattr(lgfx, "player_flip_x_set"):
            lgfx.player_flip_x_set(face_right)


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
    pressed = False
    if prev_state == 1 and state == 0:
        key = id(pin)
        now = time.ticks_ms()
        last_ms = button_last_edge_ms.get(key, None)
        if last_ms is None or time.ticks_diff(now, last_ms) >= BINARY_EDGE_DEBOUNCE_MS:
            pressed = True
            button_last_edge_ms[key] = now
    return state, pressed


def _in_rect(px, py, rect):
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return False
    return x <= px < (x + w) and y <= py < (y + h)


def _expand_rect(rect, pad):
    x, y, w, h = rect
    return (x - pad, y - pad, w + (pad * 2), h + (pad * 2))


def _release_preload_cache(reason=None):
    global preload_last_release_ms, preload_release_due_ms
    global gc_pending, perf_preload_release_count
    info = _resident_slot_info(resident_ahead_slot_id)
    if info is None or info["state"] == SLOT_STATE_EMPTY:
        return
    if not _resident_release_slot(resident_ahead_slot_id, reason):
        return
    if GC_DEFER_ENABLE:
        gc_pending = True
    else:
        gc.collect()


def _build_preload_cache(source_map_id, portal):
    started = time.ticks_ms()
    target_map_id = portal.get("target_map_id")
    config = MAP_REGISTRY.get(target_map_id)
    if not config:
        print("preload_skip_missing_target:", target_map_id)
        print("preload_ms_total:", time.ticks_diff(time.ticks_ms(), started))
        return False

    try:
        record = _resident_resolve_map_record(target_map_id, portal.get("target_spawn"))
        if not _resident_start_slot_load(resident_ahead_slot_id, record, False):
            raise RuntimeError("slot_begin_failed")
        print("preload_ready:", source_map_id, "->", target_map_id, "base:", record["tile_base"])
        return True
    except Exception as err:
        print("preload_fail:", err)
        return False
    finally:
        print("preload_ms_total:", time.ticks_diff(time.ticks_ms(), started))


def _preload_debounce_ready(px, py, rect, debounce_px):
    if debounce_px <= 0:
        return True
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return False
    left_gap = px - x
    top_gap = py - y
    right_gap = (x + w - 1) - px
    bottom_gap = (y + h - 1) - py
    return (
        left_gap >= debounce_px
        and top_gap >= debounce_px
        and right_gap >= debounce_px
        and bottom_gap >= debounce_px
    )


def _portal_direction_ok(portal, move_dx, move_dy):
    x_sign = portal.get("entry_move_x_sign")
    if x_sign == 1 and move_dx <= 0:
        return False
    if x_sign == -1 and move_dx >= 0:
        return False

    y_sign = portal.get("entry_move_y_sign")
    if y_sign == 1 and move_dy <= 0:
        return False
    if y_sign == -1 and move_dy >= 0:
        return False
    return True


def _portal_trigger_hit(portal, px, py):
    center = portal.get("trigger_center_px")
    radius = portal.get("trigger_radius_px")
    if center is not None and radius is not None:
        if len(center) >= 2 and radius > 0:
            dx = px - center[0]
            dy = py - center[1]
            return (dx * dx) + (dy * dy) <= (radius * radius)
    return _in_rect(px, py, portal["rect"])


def _get_current_portal(px, py, move_dx=0, move_dy=0):
    config = MAP_REGISTRY.get(current_map_id)
    if not config:
        return None
    portals = config.get("portals", ())
    for portal in portals:
        if _portal_trigger_hit(portal, px, py) and _portal_direction_ok(portal, move_dx, move_dy):
            return portal
    return None


def _portal_transition_clear():
    global portal_transition_active, portal_transition_started_ms, portal_transition_stage
    global portal_transition_source_map_id, portal_transition_target_map_id
    global portal_transition_target_spawn
    global portal_transition_center_screen_x, portal_transition_center_screen_y
    global portal_transition_shrink_ms, portal_transition_black_ms
    global portal_transition_portal_ref, portal_transition_last_switch_try_ms, portal_transition_switch_fail_count
    portal_transition_active = False
    portal_transition_started_ms = 0
    portal_transition_stage = "none"
    portal_transition_source_map_id = 0
    portal_transition_target_map_id = 0
    portal_transition_target_spawn = None
    portal_transition_center_screen_x = 0
    portal_transition_center_screen_y = 0
    portal_transition_shrink_ms = PORTAL_TRANSITION_DEFAULT_SHRINK_MS
    portal_transition_black_ms = PORTAL_TRANSITION_DEFAULT_BLACK_MS
    portal_transition_portal_ref = None
    portal_transition_last_switch_try_ms = 0
    portal_transition_switch_fail_count = 0


def _portal_transition_rearm_clear():
    global portal_transition_rearm_required, portal_transition_rearm_map_id, portal_transition_rearm_portal_ref
    portal_transition_rearm_required = False
    portal_transition_rearm_map_id = 0
    portal_transition_rearm_portal_ref = None


def _portal_transition_rearm_update(px, py):
    global portal_transition_rearm_required, portal_transition_rearm_map_id, portal_transition_rearm_portal_ref
    if not portal_transition_rearm_required:
        return
    portal = portal_transition_rearm_portal_ref
    if portal is None:
        _portal_transition_rearm_clear()
        return
    if current_map_id != portal_transition_rearm_map_id:
        _portal_transition_rearm_clear()
        return
    if not _portal_trigger_hit(portal, px, py):
        _portal_transition_rearm_clear()


def _portal_transition_rearm_blocked(portal):
    if not portal_transition_rearm_required:
        return False
    if current_map_id != portal_transition_rearm_map_id:
        return False
    return portal is portal_transition_rearm_portal_ref


def _portal_transition_start(portal):
    global portal_transition_active, portal_transition_started_ms, portal_transition_stage
    global portal_transition_source_map_id, portal_transition_target_map_id
    global portal_transition_target_spawn
    global portal_transition_center_screen_x, portal_transition_center_screen_y
    global portal_transition_shrink_ms, portal_transition_black_ms
    global portal_transition_portal_ref, portal_transition_last_switch_try_ms, portal_transition_switch_fail_count, explore_force_full_redraw
    global preload_zone_target_map_id, preload_zone_enter_ms, preload_release_due_ms
    global preload_last_build_ms, preload_suspend_until_ms
    # Ensure no background preload load is occupying resident ahead slot when
    # the cinematic finishes and switch_map needs to stage the target map.
    _release_preload_cache("portal_transition_start")
    preload_zone_target_map_id = None
    preload_zone_enter_ms = 0
    preload_release_due_ms = 0
    preload_last_build_ms = 0
    preload_suspend_until_ms = 0
    portal_transition_active = True
    portal_transition_started_ms = time.ticks_ms()
    portal_transition_stage = "shrink"
    portal_transition_source_map_id = current_map_id
    portal_transition_target_map_id = portal.get("target_map_id", 0)
    portal_transition_target_spawn = portal.get("target_spawn")
    portal_transition_center_screen_x = player_x - scroll_x
    portal_transition_center_screen_y = player_y - scroll_y
    portal_transition_shrink_ms = int(portal.get("transition_shrink_ms", PORTAL_TRANSITION_DEFAULT_SHRINK_MS))
    portal_transition_black_ms = int(portal.get("transition_black_ms", PORTAL_TRANSITION_DEFAULT_BLACK_MS))
    if portal_transition_shrink_ms <= 0:
        portal_transition_shrink_ms = PORTAL_TRANSITION_DEFAULT_SHRINK_MS
    if portal_transition_black_ms < 0:
        portal_transition_black_ms = PORTAL_TRANSITION_DEFAULT_BLACK_MS
    portal_transition_portal_ref = portal
    portal_transition_last_switch_try_ms = 0
    portal_transition_switch_fail_count = 0
    explore_force_full_redraw = True


def _portal_transition_update(loop_start):
    global portal_transition_stage, portal_transition_last_switch_try_ms, portal_transition_switch_fail_count
    global portal_transition_rearm_required, portal_transition_rearm_map_id, portal_transition_rearm_portal_ref
    if not portal_transition_active:
        return
    if mode != MODE_EXPLORE:
        _portal_transition_clear()
        return
    if current_map_id != portal_transition_source_map_id:
        _portal_transition_clear()
        return

    elapsed = time.ticks_diff(loop_start, portal_transition_started_ms)
    if elapsed < 0:
        elapsed = 0

    total = portal_transition_shrink_ms + portal_transition_black_ms
    if elapsed < portal_transition_shrink_ms:
        portal_transition_stage = "shrink"
        return
    if elapsed < total:
        portal_transition_stage = "black"
        return

    portal_transition_stage = "black"
    if portal_transition_last_switch_try_ms and time.ticks_diff(loop_start, portal_transition_last_switch_try_ms) < PORTAL_TRANSITION_SWITCH_RETRY_MS:
        return
    portal_transition_last_switch_try_ms = loop_start

    target_map_id = portal_transition_target_map_id
    target_spawn = portal_transition_target_spawn
    ok = False
    if target_spawn and len(target_spawn) >= 2:
        ok = bool(switch_map(target_map_id, target_spawn[0], target_spawn[1]))
    else:
        ok = bool(switch_map(target_map_id))
    if ok:
        _portal_transition_rearm_clear()
        _portal_transition_clear()
        return

    portal_transition_switch_fail_count += 1
    print(
        "portal_transition_switch_retry:",
        portal_transition_switch_fail_count,
        "target:",
        target_map_id,
    )
    if portal_transition_switch_fail_count == 1:
        _release_preload_cache("portal_transition_switch_retry")
    elif portal_transition_switch_fail_count == 2:
        _try_mount_sd()
    elif portal_transition_switch_fail_count >= PORTAL_TRANSITION_SWITCH_MAX_RETRY:
        print("portal_transition_abort_after_retries:", portal_transition_switch_fail_count)
        portal_transition_rearm_required = True
        portal_transition_rearm_map_id = portal_transition_source_map_id
        portal_transition_rearm_portal_ref = portal_transition_portal_ref
        _portal_transition_clear()
        return


def _update_preload_for_player(px, py):
    global preload_zone_target_map_id, preload_zone_enter_ms
    global preload_last_build_ms, preload_release_due_ms, preload_suspend_until_ms
    global perf_preload_build_count, perf_preload_build_fail_count
    global perf_preload_build_ms_total
    global perf_preload_skip_cached, perf_preload_skip_cooldown
    global perf_preload_skip_debounce, perf_preload_skip_dwell, perf_preload_skip_same_zone
    global perf_preload_skip_motion, perf_preload_skip_post_switch

    if resident_transition_active:
        return

    now = time.ticks_ms()
    config = MAP_REGISTRY.get(current_map_id)
    if not config:
        preload_zone_target_map_id = None
        preload_zone_enter_ms = 0
        preload_release_due_ms = 0
        _release_preload_cache("invalid_current_map")
        return

    portals = config.get("portals", ())
    preload_portal = None
    preload_zone_rect = None
    for portal in portals:
        # Keep cinematic spotlight portals out of preload by default unless a
        # portal explicitly opts in.
        if (
            portal.get("transition_effect") == PORTAL_TRANSITION_EFFECT_SPOTLIGHT
            and not portal.get("preload_allow_spotlight", False)
        ):
            continue
        preload_pad_px = portal.get("preload_pad_px", PRELOAD_PORTAL_PAD_PX)
        zone_rect = _expand_rect(portal["rect"], preload_pad_px)
        if _in_rect(px, py, zone_rect):
            preload_portal = portal
            preload_zone_rect = zone_rect
            break

    if preload_portal is None:
        preload_zone_target_map_id = None
        preload_zone_enter_ms = 0
        ahead_info = _resident_slot_info(resident_ahead_slot_id)
        if ahead_info is not None and ahead_info["state"] != SLOT_STATE_EMPTY:
            if preload_release_due_ms == 0:
                preload_release_due_ms = time.ticks_add(now, PRELOAD_RELEASE_GRACE_MS)
            elif time.ticks_diff(now, preload_release_due_ms) >= 0:
                _release_preload_cache("leave_preload_zone")
        return

    target_map_id = preload_portal.get("target_map_id")
    fast_track_target = target_map_id in PRELOAD_FAST_TRACK_TARGET_MAP_IDS
    if target_map_id == preload_zone_target_map_id:
        perf_preload_skip_same_zone += 1
    else:
        preload_zone_target_map_id = target_map_id
        preload_zone_enter_ms = now

    preload_release_due_ms = 0

    if _resident_slot_has_target(resident_ahead_slot_id, target_map_id):
        perf_preload_skip_cached += 1
        return

    if (not fast_track_target) and preload_suspend_until_ms and time.ticks_diff(now, preload_suspend_until_ms) < 0:
        perf_preload_skip_post_switch += 1
        return

    if (not fast_track_target) and (x_dir != 0 or y_dir_raw != 0):
        perf_preload_skip_motion += 1
        return

    if (not fast_track_target) and preload_zone_enter_ms and time.ticks_diff(now, preload_zone_enter_ms) < PRELOAD_DWELL_MS:
        perf_preload_skip_dwell += 1
        return

    if not _preload_debounce_ready(px, py, preload_zone_rect, PRELOAD_DEBOUNCE_PX):
        perf_preload_skip_debounce += 1
        return

    if preload_last_build_ms and time.ticks_diff(now, preload_last_build_ms) < PRELOAD_COOLDOWN_MS:
        perf_preload_skip_cooldown += 1
        return

    _release_preload_cache("retarget_preload")
    started = time.ticks_ms()
    ok = _build_preload_cache(current_map_id, preload_portal)
    perf_preload_build_ms_total += time.ticks_diff(time.ticks_ms(), started)
    preload_last_build_ms = now
    if ok:
        perf_preload_build_count += 1
    else:
        perf_preload_build_fail_count += 1


def _resident_pump_preload():
    if resident_transition_active:
        return
    info = _resident_slot_info(resident_ahead_slot_id)
    if info is None or info["state"] != SLOT_STATE_LOADING:
        return
    pumped = lgfx.slot_pump_load(resident_ahead_slot_id, PRELOAD_BUDGET_BYTES)
    if pumped < 0:
        print("preload_pump_fail:", resident_ahead_slot_id, _resident_slot_info(resident_ahead_slot_id))
    elif pumped > 0:
        updated = _resident_slot_info(resident_ahead_slot_id)
        if updated and updated["state"] == SLOT_STATE_READY:
            print("preload_slot_ready:", resident_slots[resident_ahead_slot_id]["map_id"])
            _resident_log_slots("preload_slot")


def _maybe_run_deferred_gc(loop_start, moved, scrolled):
    global gc_pending, gc_last_run_ms, gc_suspend_until_ms
    global perf_gc_run_count, perf_gc_run_ms_total

    if not gc_pending:
        return False
    if gc_suspend_until_ms and time.ticks_diff(loop_start, gc_suspend_until_ms) < 0:
        return False
    if not GC_DEFER_ENABLE:
        started = time.ticks_ms()
        gc.collect()
        perf_gc_run_count += 1
        perf_gc_run_ms_total += time.ticks_diff(time.ticks_ms(), started)
        gc_pending = False
        gc_last_run_ms = loop_start
        return True
    if gc_last_run_ms and time.ticks_diff(loop_start, gc_last_run_ms) < GC_DEFER_MIN_INTERVAL_MS:
        return False
    if GC_DEFER_IDLE_ONLY:
        if mode != MODE_EXPLORE:
            return False
        if moved or scrolled:
            return False
    started = time.ticks_ms()
    gc.collect()
    perf_gc_run_count += 1
    perf_gc_run_ms_total += time.ticks_diff(time.ticks_ms(), started)
    gc_pending = False
    gc_last_run_ms = loop_start
    return True


def _get_move_step_for_map(map_id):
    if map_id in WOOD_SLOW_MAP_IDS:
        return WOOD_ROOM_MOVE_STEP
    return MOVE_STEP


def _is_wood_map(map_id):
    return map_id in WOOD_SLOW_MAP_IDS


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
    delta = int(delta)
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

    move_step = _get_move_step_for_map(current_map_id)
    dx, move_carry_x = _scaled_axis_delta(x_dir, move_step, frame_dt, move_carry_x)
    dy_raw, move_carry_y = _scaled_axis_delta(y_dir_raw, move_step, frame_dt, move_carry_y)

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
            anim_step_ms = PLAYER_ANIM_STEP_MS
            if _is_wood_map(current_map_id):
                anim_step_ms = WOOD_PLAYER_ANIM_STEP_MS
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, anim_last_ms) >= anim_step_ms:
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


def _menu_nav_dir_horizontal():
    if x_dir > 0:
        return 1
    if x_dir < 0:
        return -1
    return 0


def _draw_title_menu_screen(loop_start, full_redraw):
    global title_cover_drew_png

    if full_redraw:
        lgfx.clear()
        drew_cover = False
        if title_cover_path and hasattr(lgfx, "draw_png_file"):
            try:
                drew_cover = bool(lgfx.draw_png_file(title_cover_path, 0, 0, ACTIVE_VIEW_W, ACTIVE_VIEW_H))
            except Exception:
                drew_cover = False
        if not drew_cover:
            _fill_rect_solid(0, 0, ACTIVE_VIEW_W, ACTIVE_VIEW_H, 0x0000)
        title_cover_drew_png = drew_cover
    else:
        drew_cover = title_cover_drew_png

    ui_drawn = False
    if hasattr(lgfx, "draw_png_file"):
        ui_path = title_ui_start_path if title_menu_index == 0 else title_ui_continue_path
        if ui_path:
            try:
                ui_drawn = bool(lgfx.draw_png_file(ui_path, TITLE_UI_X, TITLE_UI_Y, TITLE_UI_W, TITLE_UI_H))
            except Exception:
                ui_drawn = False

    option_rects = (TITLE_OPTION_NEW_GAME_RECT, TITLE_OPTION_CONTINUE_RECT)
    if drew_cover and ui_drawn:
        pass
    elif drew_cover:
        for i, rect in enumerate(option_rects):
            rx, ry, rw, rh = rect
            if i == title_menu_index:
                _draw_rect_thick(rx, ry, rw, rh, BATTLE_CMD_COLOR, 2)
            else:
                _draw_rect_thick(rx, ry, rw, rh, BATTLE_COLOR_WHITE, 1)
    else:
        panel_w = 136
        panel_h = 66
        panel_x = 8
        panel_y = ACTIVE_VIEW_H - panel_h - 12
        _fill_rect_solid(panel_x, panel_y, panel_w, panel_h, 0x0000)
        _draw_rect_thick(panel_x, panel_y, panel_w, panel_h, BATTLE_COLOR_WHITE, 2)

        labels = (TITLE_MENU_NEW_GAME, TITLE_MENU_CONTINUE)
        row_h = 24
        row_y0 = panel_y + 8
        for i, label in enumerate(labels):
            row_y = row_y0 + (i * row_h)
            if i == title_menu_index:
                _fill_rect_solid(panel_x + 6, row_y, panel_w - 12, row_h - 2, 0x4208)
                _draw_rect_thick(panel_x + 6, row_y, panel_w - 12, row_h - 2, BATTLE_CMD_COLOR, 1)
                text_color = BATTLE_CMD_COLOR
            else:
                text_color = BATTLE_COLOR_WHITE
            _draw_text_in_box(panel_x + 8, row_y, panel_w - 16, row_h - 2, label, text_color)

    if title_notice_text and time.ticks_diff(title_notice_until_ms, loop_start) > 0:
        notice_h = 20
        if drew_cover:
            notice_w = 136
            notice_x = 8
            notice_y = TITLE_OPTION_NEW_GAME_RECT[1] - notice_h - 8
        else:
            notice_w = panel_w
            notice_x = panel_x
            notice_y = panel_y - notice_h - 6
        if notice_y < 6:
            notice_y = 6
        _fill_rect_solid(notice_x, notice_y, notice_w, notice_h, 0x0000)
        _draw_rect_thick(notice_x, notice_y, notice_w, notice_h, BATTLE_COLOR_WHITE, 1)
        _draw_text_in_box(notice_x + 4, notice_y + 2, notice_w - 8, notice_h - 4, title_notice_text, BATTLE_COLOR_WHITE)


def update_title_menu(loop_start, interact_pressed):
    global mode, title_menu_index, title_nav_prev_dir, title_nav_next_ms
    global title_notice_until_ms, title_notice_text, title_dirty, title_full_redraw
    global explore_force_full_redraw, spawn_intro_needs_redraw

    if title_notice_text and time.ticks_diff(title_notice_until_ms, loop_start) <= 0:
        title_notice_text = None
        title_notice_until_ms = 0
        title_dirty = True
        title_full_redraw = True

    nav_dir = _menu_nav_dir_vertical()
    if nav_dir == 0:
        title_nav_prev_dir = 0
    elif nav_dir != title_nav_prev_dir:
        if time.ticks_diff(loop_start, title_nav_next_ms) >= 0:
            if nav_dir > 0:
                title_menu_index = (title_menu_index + 1) % 2
            else:
                title_menu_index = (title_menu_index - 1 + 2) % 2
            title_nav_next_ms = time.ticks_add(loop_start, TITLE_NAV_SWITCH_COOLDOWN_MS)
            title_dirty = True
        title_nav_prev_dir = nav_dir

    if not interact_pressed:
        return

    if title_menu_index == 0:
        title_notice_text = None
        title_notice_until_ms = 0
        mode = MODE_EXPLORE
        explore_force_full_redraw = True
        spawn_intro_needs_redraw = spawn_intro_active
        title_dirty = True
        return

    if title_menu_index == 1:
        if _path_exists(config.SAVE1_PATH):
            title_notice_text = TITLE_NOTICE_CONTINUE_TEXT
        else:
            title_notice_text = TITLE_NOTICE_NO_SAVE_TEXT
        title_notice_until_ms = time.ticks_add(loop_start, TITLE_NOTICE_MS)
        title_dirty = True
        title_full_redraw = True
        return


def _open_explore_inventory():
    global mode, inv_choice_index, inv_nav_prev_dir
    global inv_drop_active, inv_drop_choice_index, inv_drop_choice_count, inv_drop_nav_prev_dir, inv_screen_dirty
    global inv_tab_index, inv_tab_active, inv_tab_nav_prev_dir
    global inv_focus_side, inv_focus_nav_prev_dir

    mode = MODE_EXPLORE_INVENTORY
    inv_choice_index = inventory_clamp_index(inv_choice_index)
    inv_nav_prev_dir = 0
    inv_drop_active = False
    inv_drop_choice_index = 0
    inv_drop_choice_count = 2
    inv_drop_nav_prev_dir = 0
    inv_tab_index = INV_TAB_ITEM
    inv_tab_active = INV_TAB_ITEM
    inv_tab_nav_prev_dir = 0
    inv_focus_side = INV_FOCUS_LEFT
    inv_focus_nav_prev_dir = 0
    inv_screen_dirty = True


def _close_explore_inventory():
    global mode, explore_force_full_redraw
    global inv_nav_prev_dir, inv_drop_active, inv_drop_choice_index, inv_drop_choice_count, inv_drop_nav_prev_dir, inv_screen_dirty
    global inv_tab_nav_prev_dir
    global inv_focus_side, inv_focus_nav_prev_dir

    mode = MODE_EXPLORE
    explore_force_full_redraw = True
    inv_nav_prev_dir = 0
    inv_drop_active = False
    inv_drop_choice_index = 0
    inv_drop_choice_count = 2
    inv_drop_nav_prev_dir = 0
    inv_tab_nav_prev_dir = 0
    inv_focus_side = INV_FOCUS_LEFT
    inv_focus_nav_prev_dir = 0
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
                if i == inv_choice_index and ((inv_focus_side == INV_FOCUS_RIGHT) or inv_drop_active):
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
    menu_h = 66 if inv_drop_choice_count > 2 else 52
    menu_x = right_x + (right_w - menu_w) // 2
    menu_y = right_y + (right_h - menu_h) // 2
    _fill_rect_solid(menu_x, menu_y, menu_w, menu_h, 0x0000)
    _draw_rect_thick(menu_x, menu_y, menu_w, menu_h, BATTLE_COLOR_WHITE, panel_border)
    selected_item = None
    if inv_choice_index >= 0 and inv_choice_index < len(inventory_items):
        selected_item = inventory_items[inv_choice_index]
    if _is_weapon_item(selected_item):
        labels = ("EQUIP", "DROP", "KEEP")
    else:
        labels = ("KEEP", "DROP")
    row_h = 20
    base_y = menu_y + 6
    for i, label in enumerate(labels):
        text_color = BATTLE_COLOR_RED if inv_drop_choice_index == i else BATTLE_COLOR_WHITE
        _draw_text_in_box(menu_x + 4, base_y + (i * row_h), menu_w - 8, 16, label, text_color)


def update_explore_inventory(loop_start, item_pressed, interact_pressed):
    del loop_start
    global inv_choice_index, inv_nav_prev_dir
    global inv_drop_active, inv_drop_choice_index, inv_drop_nav_prev_dir
    global inv_drop_choice_count
    global inv_screen_dirty
    global inv_tab_index, inv_tab_active, inv_tab_nav_prev_dir
    global inv_focus_side, inv_focus_nav_prev_dir

    if item_pressed:
        _close_explore_inventory()
        return

    if inv_drop_active:
        nav_dir = _menu_nav_dir_vertical()
        if nav_dir != 0 and nav_dir != inv_drop_nav_prev_dir:
            if inv_drop_choice_count < 2:
                inv_drop_choice_count = 2
            if nav_dir > 0:
                inv_drop_choice_index = (inv_drop_choice_index + inv_drop_choice_count - 1) % inv_drop_choice_count
            else:
                inv_drop_choice_index = (inv_drop_choice_index + 1) % inv_drop_choice_count
            inv_screen_dirty = True
        inv_drop_nav_prev_dir = nav_dir
        if not interact_pressed:
            return
        if inv_choice_index >= 0 and inv_choice_index < len(inventory_items):
            selected_item = inventory_items[inv_choice_index]
            if _is_weapon_item(selected_item):
                if inv_drop_choice_index == 0:
                    _equip_inventory_item(selected_item)
                elif inv_drop_choice_index == 1:
                    _drop_inventory_item_at(inv_choice_index)
            else:
                if inv_drop_choice_index == 1:
                    _drop_inventory_item_at(inv_choice_index)
            inv_choice_index = inventory_clamp_index(inv_choice_index)
        inv_drop_active = False
        inv_drop_choice_index = 0
        inv_drop_choice_count = 2
        inv_drop_nav_prev_dir = 0
        inv_screen_dirty = True
        return

    focus_dir = _menu_nav_dir_horizontal()
    if inv_tab_active == INV_TAB_STAT:
        if inv_focus_side != INV_FOCUS_LEFT:
            inv_focus_side = INV_FOCUS_LEFT
            inv_screen_dirty = True
        inv_focus_nav_prev_dir = 0
    else:
        if focus_dir != 0 and focus_dir != inv_focus_nav_prev_dir:
            if focus_dir > 0:
                if inv_focus_side != INV_FOCUS_RIGHT:
                    inv_focus_side = INV_FOCUS_RIGHT
                    inv_screen_dirty = True
            else:
                if inv_focus_side != INV_FOCUS_LEFT:
                    inv_focus_side = INV_FOCUS_LEFT
                    inv_screen_dirty = True
        inv_focus_nav_prev_dir = focus_dir

    if inventory_is_empty():
        inv_choice_index = 0

    nav_dir = _menu_nav_dir_vertical()
    if inv_focus_side == INV_FOCUS_LEFT:
        if nav_dir != 0 and nav_dir != inv_tab_nav_prev_dir:
            inv_tab_index = (inv_tab_index + 1) % 2
            if inv_tab_active != inv_tab_index:
                inv_tab_active = inv_tab_index
                inv_drop_active = False
                inv_drop_choice_index = 0
                inv_drop_choice_count = 2
                inv_drop_nav_prev_dir = 0
                if inv_tab_active == INV_TAB_STAT:
                    inv_focus_side = INV_FOCUS_LEFT
                inv_screen_dirty = True
        inv_tab_nav_prev_dir = nav_dir
        inv_nav_prev_dir = 0
    else:
        inv_tab_nav_prev_dir = 0
        if inv_tab_active == INV_TAB_ITEM:
            if nav_dir != 0 and nav_dir != inv_nav_prev_dir and not inventory_is_empty():
                count = len(inventory_items)
                if nav_dir > 0:
                    inv_choice_index = (inv_choice_index + 1) % count
                else:
                    inv_choice_index = (inv_choice_index - 1 + count) % count
                inv_screen_dirty = True
            inv_nav_prev_dir = nav_dir
        else:
            inv_nav_prev_dir = 0

    if interact_pressed:
        if inv_focus_side == INV_FOCUS_LEFT:
            return
        if inv_tab_active == INV_TAB_STAT:
            return
        if not inventory_is_empty():
            selected_item = inventory_items[inv_choice_index] if inv_choice_index < len(inventory_items) else None
            inv_drop_active = True
            if _is_weapon_item(selected_item):
                inv_drop_choice_count = 3
                inv_drop_choice_index = 2  # KEEP
            else:
                inv_drop_choice_count = 2
                inv_drop_choice_index = 0
            inv_drop_nav_prev_dir = 0
            inv_screen_dirty = True
        return

    if inv_focus_side == INV_FOCUS_LEFT:
        inv_nav_prev_dir = 0


def _draw_spotlight_mask(cx, cy, r, view_w, view_h):
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


def _draw_spawn_intro_overlay():
    cx = player_x - scroll_x
    cy = player_y - scroll_y
    view_w = ACTIVE_VIEW_W
    view_h = ACTIVE_VIEW_H
    _draw_spotlight_mask(cx, cy, SPAWN_SPOTLIGHT_RADIUS, view_w, view_h)

    if spawn_intro_overlay_path and hasattr(lgfx, "draw_png_file"):
        lgfx.draw_png_file(
            spawn_intro_overlay_path,
            cx - (PLAYER_FRAME_W // 2),
            cy - (PLAYER_FRAME_H // 2),
            PLAYER_FRAME_W,
            PLAYER_FRAME_H,
        )


def _draw_portal_transition_overlay(loop_start):
    if not portal_transition_active:
        return
    elapsed = time.ticks_diff(loop_start, portal_transition_started_ms)
    if elapsed < 0:
        elapsed = 0
    if elapsed >= portal_transition_shrink_ms:
        _fill_rect_solid(0, 0, ACTIVE_VIEW_W, ACTIVE_VIEW_H, 0x0000)
        return

    cx = portal_transition_center_screen_x
    cy = portal_transition_center_screen_y
    if cx < 0:
        cx = 0
    elif cx >= ACTIVE_VIEW_W:
        cx = ACTIVE_VIEW_W - 1
    if cy < 0:
        cy = 0
    elif cy >= ACTIVE_VIEW_H:
        cy = ACTIVE_VIEW_H - 1

    dx = cx if cx > (ACTIVE_VIEW_W - 1 - cx) else (ACTIVE_VIEW_W - 1 - cx)
    dy = cy if cy > (ACTIVE_VIEW_H - 1 - cy) else (ACTIVE_VIEW_H - 1 - cy)
    max_r = _isqrt((dx * dx) + (dy * dy)) + 2
    remain = portal_transition_shrink_ms - elapsed
    if remain < 0:
        remain = 0
    r = (max_r * remain) // portal_transition_shrink_ms
    _draw_spotlight_mask(cx, cy, r, ACTIVE_VIEW_W, ACTIVE_VIEW_H)


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


def _player_touches_rect(rect, pad=0):
    rx, ry, rw, rh = rect
    if rw <= 0 or rh <= 0:
        return False
    pr = PLAYER_R + pad
    px = player_x - pr
    py = player_y - pr
    pw = pr * 2 + 1
    ph = pr * 2 + 1
    return _rects_intersect(px, py, pw, ph, rx, ry, rw, rh)


def _find_nearby_ground_weapon_drop():
    radius2 = GROUND_WEAPON_PICKUP_RADIUS * GROUND_WEAPON_PICKUP_RADIUS
    for i, drop in enumerate(ground_weapon_drops):
        if drop.get("map_id") != current_map_id:
            continue
        dx = int(drop.get("x", 0)) - player_x
        dy = int(drop.get("y", 0)) - player_y
        if (dx * dx) + (dy * dy) <= radius2:
            return i
    return -1


def _find_wood_right_rack_pickup():
    if current_map_id != WOOD_RIGHT_ID:
        return None
    best_rack = None
    best_d2 = 0
    radius2 = WOOD_RIGHT_WEAPON_PICKUP_RADIUS * WOOD_RIGHT_WEAPON_PICKUP_RADIUS
    for rack in WOOD_RIGHT_WEAPON_RACKS:
        pickup_id = rack.get("pickup_id")
        if rack_pickup_taken.get(pickup_id):
            continue
        rx = int(rack.get("interact_x", 0))
        ry = int(rack.get("interact_y", 0))
        if rx > 0 or ry > 0:
            dx = rx - player_x
            dy = ry - player_y
            d2 = (dx * dx) + (dy * dy)
            if d2 <= radius2:
                if (best_rack is None) or (d2 < best_d2):
                    best_rack = rack
                    best_d2 = d2
        rack_rect = rack.get("rect", (0, 0, 0, 0))
        if _player_touches_rect(rack_rect, 2) or _in_rect(player_x, player_y, rack_rect):
            return rack
    return best_rack


def _try_open_weapon_pickup_dialog():
    global weapon_pickup_dialog_active, weapon_pickup_choice_index
    global weapon_pickup_nav_prev_dir, weapon_pickup_target
    global weapon_pickup_dialog_dirty

    ground_index = _find_nearby_ground_weapon_drop()
    if ground_index >= 0 and ground_index < len(ground_weapon_drops):
        drop = ground_weapon_drops[ground_index]
        item = drop.get("item")
        if item:
            weapon_pickup_target = {
                "source": "ground",
                "drop_id": drop.get("id"),
                "item": item,
            }
            weapon_pickup_dialog_active = True
            weapon_pickup_choice_index = 0
            weapon_pickup_nav_prev_dir = 0
            weapon_pickup_dialog_dirty = True
            return True

    rack = _find_wood_right_rack_pickup()
    if rack:
        base_item = rack.get("item")
        item = _inventory_clone_item(base_item) if base_item else None
        if item:
            item["origin_pickup_id"] = rack.get("pickup_id")
            weapon_pickup_target = {
                "source": "rack",
                "pickup_id": rack.get("pickup_id"),
                "item": item,
            }
            weapon_pickup_dialog_active = True
            weapon_pickup_choice_index = 0
            weapon_pickup_nav_prev_dir = 0
            weapon_pickup_dialog_dirty = True
            return True
    return False


def _resolve_weapon_pickup_confirm():
    global weapon_pickup_dialog_active, weapon_pickup_choice_index
    global weapon_pickup_nav_prev_dir, weapon_pickup_target
    global explore_force_full_redraw, weapon_pickup_dialog_dirty

    target = weapon_pickup_target
    if weapon_pickup_choice_index != 0 or not target:
        weapon_pickup_dialog_active = False
        weapon_pickup_choice_index = 0
        weapon_pickup_nav_prev_dir = 0
        weapon_pickup_target = None
        weapon_pickup_dialog_dirty = False
        explore_force_full_redraw = True
        return

    if inventory_try_add(target.get("item")):
        source = target.get("source")
        if source == "rack":
            pickup_id = target.get("pickup_id")
            if pickup_id:
                rack_pickup_taken[pickup_id] = True
        elif source == "ground":
            drop_id = target.get("drop_id")
            if drop_id:
                for i in range(len(ground_weapon_drops) - 1, -1, -1):
                    if ground_weapon_drops[i].get("id") == drop_id:
                        ground_weapon_drops.pop(i)
                        break

    weapon_pickup_dialog_active = False
    weapon_pickup_choice_index = 0
    weapon_pickup_nav_prev_dir = 0
    weapon_pickup_target = None
    weapon_pickup_dialog_dirty = False
    explore_force_full_redraw = True


def update_weapon_pickup_dialog(interact_pressed):
    global weapon_pickup_choice_index, weapon_pickup_nav_prev_dir, weapon_pickup_dialog_dirty
    if not weapon_pickup_dialog_active:
        return
    nav_dir = _menu_nav_dir_horizontal()
    if nav_dir != 0 and nav_dir != weapon_pickup_nav_prev_dir:
        weapon_pickup_choice_index = 1 - weapon_pickup_choice_index
        weapon_pickup_dialog_dirty = True
    weapon_pickup_nav_prev_dir = nav_dir
    if interact_pressed:
        _resolve_weapon_pickup_confirm()


def _draw_ground_weapon_drops():
    for drop in ground_weapon_drops:
        if drop.get("map_id") != current_map_id:
            continue
        sx = int(drop.get("x", 0)) - scroll_x
        sy = int(drop.get("y", 0)) - scroll_y
        if sx < 0 or sy < 0 or sx >= ACTIVE_VIEW_W or sy >= ACTIVE_VIEW_H:
            continue
        lgfx.draw_circle(sx, sy, GROUND_DROP_MARKER_R, BATTLE_COLOR_WHITE)


def _map6_boss_should_draw():
    if current_map_id != MAP6_ID:
        return False
    if map6_boss_defeated:
        return False
    if not map6_boss_sheet_loaded:
        return False
    if not hasattr(lgfx, "enemy_draw") or not hasattr(lgfx, "enemy_frame_set"):
        return False
    return True


def _map6_boss_draw_rect():
    half_w = MAP6_BOSS_FRAME_W // 2
    half_h = MAP6_BOSS_FRAME_H // 2
    return (
        MAP6_BOSS_CENTER_X - half_w - scroll_x,
        MAP6_BOSS_CENTER_Y - half_h - scroll_y,
        MAP6_BOSS_FRAME_W,
        MAP6_BOSS_FRAME_H,
    )


def _map6_boss_player_overlap():
    bx, by, bw, bh = _map6_boss_draw_rect()
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
    return _rects_intersect(px, py, pw, ph, bx, by, bw, bh)


def _map6_boss_update_anim(loop_start):
    global map6_boss_anim_seq_index, map6_boss_anim_last_ms
    if map6_boss_anim_last_ms == 0:
        map6_boss_anim_last_ms = loop_start
    while time.ticks_diff(loop_start, map6_boss_anim_last_ms) >= MAP6_BOSS_ANIM_FRAME_MS:
        map6_boss_anim_last_ms = time.ticks_add(map6_boss_anim_last_ms, MAP6_BOSS_ANIM_FRAME_MS)
        map6_boss_anim_seq_index += 1
        if map6_boss_anim_seq_index >= len(MAP6_BOSS_ANIM_SEQUENCE):
            map6_boss_anim_seq_index = 0


def _draw_map6_boss(loop_start, scene_redrawn=False, player_redrawn=False):
    global map6_boss_last_draw_frame, map6_boss_last_draw_sx, map6_boss_last_draw_sy
    if not _map6_boss_should_draw():
        map6_boss_last_draw_frame = -1
        return
    _map6_boss_update_anim(loop_start)
    frame_index = MAP6_BOSS_ANIM_SEQUENCE[map6_boss_anim_seq_index]
    sx = MAP6_BOSS_CENTER_X - scroll_x
    sy = MAP6_BOSS_CENTER_Y - scroll_y
    need_draw = scene_redrawn or (frame_index != map6_boss_last_draw_frame) or (sx != map6_boss_last_draw_sx) or (sy != map6_boss_last_draw_sy)
    if (not need_draw) and player_redrawn:
        need_draw = _map6_boss_player_overlap()
    if not need_draw:
        return
    lgfx.enemy_frame_set(frame_index)
    lgfx.enemy_draw(sx, sy)
    map6_boss_last_draw_frame = frame_index
    map6_boss_last_draw_sx = sx
    map6_boss_last_draw_sy = sy


def _map6_boss_trigger_hit(px, py):
    if current_map_id != MAP6_ID or map6_boss_defeated or (not map6_boss_sheet_loaded):
        return False
    dx = px - MAP6_BOSS_CENTER_X
    dy = py - MAP6_BOSS_CENTER_Y
    r = MAP6_BOSS_TRIGGER_RADIUS_PX
    return (dx * dx + dy * dy) <= (r * r)


def _map6_boss_mark_defeated():
    global map6_boss_defeated, map6_boss_battle_active, map6_boss_last_draw_frame
    map6_boss_defeated = True
    map6_boss_battle_active = False
    map6_boss_last_draw_frame = -1


def _draw_weapon_pickup_dialog():
    if not weapon_pickup_dialog_active:
        return
    target = weapon_pickup_target if weapon_pickup_target else {}
    item = target.get("item", {})
    item_name = item.get("name", "Weapon")
    dialog_w = 280
    if dialog_w > ACTIVE_VIEW_W - 8:
        dialog_w = ACTIVE_VIEW_W - 8
    dialog_h = 54
    dialog_x = (ACTIVE_VIEW_W - dialog_w) // 2
    dialog_y = ACTIVE_VIEW_H - dialog_h - 8
    if dialog_y < 4:
        dialog_y = 4

    _fill_rect_solid(dialog_x, dialog_y, dialog_w, dialog_h, 0x0000)
    _draw_rect_thick(dialog_x, dialog_y, dialog_w, dialog_h, BATTLE_COLOR_WHITE, BATTLE_CMD_BORDER_THICK)
    _draw_text_in_box(dialog_x + 8, dialog_y + 8, dialog_w - 16, 16, "Pick up %s?" % item_name, BATTLE_COLOR_WHITE)

    yes_text = ">YES" if weapon_pickup_choice_index == 0 else " YES"
    no_text = ">NO" if weapon_pickup_choice_index == 1 else " NO"
    yes_w = 40
    no_w = 32
    no_x = dialog_x + dialog_w - no_w - 12
    yes_x = no_x - yes_w - 8
    options_y = dialog_y + dialog_h - 20
    _draw_text_in_box(yes_x, options_y, yes_w, 12, yes_text, BATTLE_COLOR_WHITE)
    _draw_text_in_box(no_x, options_y, no_w, 12, no_text, BATTLE_COLOR_WHITE)


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


def _clear_rect_black_in_battle_interior(frame_x, frame_y, frame_w, x, y, w, h):
    if w <= 0 or h <= 0:
        return
    pad = BATTLE_FRAME_BORDER_THICK
    inner_x0 = frame_x + pad
    inner_y0 = frame_y + pad
    inner_x1 = frame_x + frame_w - pad
    inner_y1 = frame_y + BATTLE_FRAME_H - pad
    x0 = x if x > inner_x0 else inner_x0
    y0 = y if y > inner_y0 else inner_y0
    x1 = x + w
    y1 = y + h
    if x1 > inner_x1:
        x1 = inner_x1
    if y1 > inner_y1:
        y1 = inner_y1
    if x1 <= x0 or y1 <= y0:
        return
    _clear_rect_black(x0, y0, x1 - x0, y1 - y0)


def _clear_rect_black_around_battle(frame_x, frame_y, frame_w, x, y, w, h):
    if w <= 0 or h <= 0:
        return
    x0 = x
    y0 = y
    x1 = x + w
    y1 = y + h
    frame_x0 = frame_x
    frame_y0 = frame_y
    frame_x1 = frame_x + frame_w
    frame_y1 = frame_y + BATTLE_FRAME_H
    row_y0 = y0 if y0 > frame_y0 else frame_y0
    row_y1 = y1 if y1 < frame_y1 else frame_y1
    if row_y1 <= row_y0:
        return
    if x0 < frame_x0:
        _clear_rect_black(x0, row_y0, frame_x0 - x0, row_y1 - row_y0)
    if x1 > frame_x1:
        _clear_rect_black(frame_x1, row_y0, x1 - frame_x1, row_y1 - row_y0)


def _clear_story_prev_delta(
    frame_x,
    frame_y,
    frame_w,
    prev_x,
    prev_y,
    curr_x,
    curr_y,
    w,
    h,
    pad=2,
    include_outside=False,
    overlap_strip=0,
):
    if w <= 0 or h <= 0:
        return
    px0 = prev_x - pad
    py0 = prev_y - pad
    px1 = prev_x + w + pad
    py1 = prev_y + h + pad
    cx0 = curr_x - pad
    cy0 = curr_y - pad
    cx1 = curr_x + w + pad
    cy1 = curr_y + h + pad

    ix0 = px0 if px0 > cx0 else cx0
    iy0 = py0 if py0 > cy0 else cy0
    ix1 = px1 if px1 < cx1 else cx1
    iy1 = py1 if py1 < cy1 else cy1

    def _clear_piece(x, y, cw, ch):
        if cw <= 0 or ch <= 0:
            return
        _clear_rect_black_in_battle_interior(frame_x, frame_y, frame_w, x, y, cw, ch)
        if include_outside:
            _clear_rect_black_around_battle(frame_x, frame_y, frame_w, x, y, cw, ch)

    if ix1 <= ix0 or iy1 <= iy0:
        _clear_piece(px0, py0, px1 - px0, py1 - py0)
        return

    # top
    _clear_piece(px0, py0, px1 - px0, iy0 - py0)
    # bottom
    _clear_piece(px0, iy1, px1 - px0, py1 - iy1)
    # left
    _clear_piece(px0, iy0, ix0 - px0, iy1 - iy0)
    # right
    _clear_piece(ix1, iy0, px1 - ix1, iy1 - iy0)

    # Clear a thin strip on the overlap trailing side to remove alpha-edge residue
    # without resorting to full previous-frame clears.
    if overlap_strip > 0:
        t = overlap_strip
        dx = curr_x - prev_x
        dy = curr_y - prev_y
        ow = ix1 - ix0
        oh = iy1 - iy0
        if ow > 0 and oh > 0:
            if t > ow:
                t = ow
            if dx < 0:
                _clear_piece(ix1 - t, iy0, t, oh)
            elif dx > 0:
                _clear_piece(ix0, iy0, t, oh)
            t2 = overlap_strip if overlap_strip <= oh else oh
            if dy < 0:
                _clear_piece(ix0, iy1 - t2, ow, t2)
            elif dy > 0:
                _clear_piece(ix0, iy0, ow, t2)


def _clear_story_curr_fringe(frame_x, frame_y, frame_w, x, y, w, h, fringe=1):
    if w <= 0 or h <= 0:
        return
    t = fringe if fringe > 0 else 1
    if t > (w // 2):
        t = w // 2
    if t > (h // 2):
        t = h // 2
    if t < 1:
        t = 1
    # top / bottom
    _clear_rect_black_in_battle_interior(frame_x, frame_y, frame_w, x - t, y - t, w + (t * 2), t)
    _clear_rect_black_in_battle_interior(frame_x, frame_y, frame_w, x - t, y + h, w + (t * 2), t)
    # left / right
    _clear_rect_black_in_battle_interior(frame_x, frame_y, frame_w, x - t, y, t, h)
    _clear_rect_black_in_battle_interior(frame_x, frame_y, frame_w, x + w, y, t, h)


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


def _map1_story_dialog_safe_rect(frame_x, frame_y, frame_w, cmd_y):
    status_y = cmd_y - (8 + BATTLE_STATUS_TO_CMD_GAP)
    status_band_top = status_y - BATTLE_HP_BAR_H - 3
    y_min = frame_y + 10
    y_max = status_band_top - 4
    if y_max <= y_min:
        y_max = y_min + 20

    enemy_left = battle_menu_enemy_x
    enemy_right = enemy_left + battle_menu_enemy_w
    enemy_mid_y = battle_menu_enemy_y + (battle_menu_enemy_h // 2)

    src_w = MAP1_STORY_LINE_PNG_W
    src_h = MAP1_STORY_LINE_PNG_H
    # Keep text visually larger than the previous auto-shrink behavior.
    desired_w = 162 if _map1_story_is_toriel_lines() else 164
    if desired_w > src_w + 4:
        desired_w = src_w + 4

    if _map1_story_is_toriel_lines():
        toriel_left = map1_story_toriel_x
        if toriel_left <= 0:
            toriel_left = frame_x + frame_w - MAP1_STORY_TORIEL_DRAW_W - 4
        side_left = frame_x + 8
        side_right = toriel_left - 4
        if side_right <= side_left + 20:
            side_right = side_left + 20
        avail_w = side_right - side_left
        dialog_w = desired_w
        if dialog_w > avail_w - 4:
            dialog_w = avail_w - 4
        if dialog_w < 40:
            dialog_w = 40
        dialog_h = (dialog_w * src_h) // src_w
        if dialog_h < 20:
            dialog_h = 20
        dialog_left = side_right - dialog_w - 1
        if dialog_left < side_left:
            dialog_left = side_left
    else:
        side_left = enemy_right + 6
        side_right = frame_x + frame_w - 8
        if side_right <= side_left + 20:
            side_right = side_left + 20
        avail_w = side_right - side_left
        dialog_w = desired_w
        if dialog_w > avail_w - 4:
            dialog_w = avail_w - 4
        if dialog_w < 40:
            dialog_w = 40
        dialog_h = (dialog_w * src_h) // src_w
        if dialog_h < 20:
            dialog_h = 20
        # Keep box beside FLOWEY, not pinned to screen edge.
        dialog_left = side_left + 2
        if dialog_left + dialog_w > side_right:
            dialog_left = side_right - dialog_w
        if dialog_left < side_left:
            dialog_left = side_left

    dialog_top = enemy_mid_y - (dialog_h // 2)
    if dialog_top < y_min:
        dialog_top = y_min
    if dialog_top + dialog_h > y_max:
        dialog_top = y_max - dialog_h
        if dialog_top < y_min:
            dialog_top = y_min

    return dialog_left, dialog_top, dialog_w, dialog_h


def _draw_battle_menu_static_layer(frame_x, frame_y, frame_w, cmd_x0, cmd_y, cmd_w):
    global battle_menu_enemy_x, battle_menu_enemy_y, battle_menu_enemy_w, battle_menu_enemy_h
    global map1_enemy_anchor_mode
    global map1_story_fire_prev_x, map1_story_fire_prev_y, map1_story_fire_prev_valid
    global map1_story_toriel_prev_x, map1_story_toriel_prev_y, map1_story_toriel_prev_valid, map1_story_prev_flowey_visible

    _draw_battle_frame(frame_x, frame_y, frame_w, BATTLE_FRAME_H)

    enemy_sprite_path, enemy_sprite_w, enemy_sprite_h = _battle_enemy_sprite_info()
    enemy_x = frame_x + ((frame_w - enemy_sprite_w) // 2)
    if _map1_story_is_active():
        enemy_sprite_path = _map1_story_enemy_sprite_path()
        enemy_sprite_w = MAP1_STORY_ENEMY_DRAW_W
        enemy_sprite_h = MAP1_STORY_ENEMY_DRAW_H
        center_x = frame_x + ((frame_w - enemy_sprite_w) // 2)
        left_x = frame_x + 4
        if map1_enemy_anchor_mode == MAP1_ENEMY_ANCHOR_LEFT:
            enemy_x = left_x
        elif map1_enemy_anchor_mode == MAP1_ENEMY_ANCHOR_SLIDING_LEFT:
            elapsed = time.ticks_diff(time.ticks_ms(), map1_enemy_slide_start_ms)
            if elapsed < 0:
                elapsed = 0
            if elapsed >= MAP1_STORY_ENEMY_SLIDE_MS:
                enemy_x = left_x
                map1_enemy_anchor_mode = MAP1_ENEMY_ANCHOR_LEFT
            else:
                enemy_x = center_x + (((left_x - center_x) * elapsed) // MAP1_STORY_ENEMY_SLIDE_MS)
    enemy_y = frame_y + 10 if _map1_story_is_active() else (frame_y + 16)
    enemy_bottom = enemy_y + enemy_sprite_h
    enemy_drawn = False

    if _map1_story_is_active():
        flowey_visible = not map1_story_flowey_hidden
        if (not flowey_visible) and map1_story_prev_flowey_visible:
            _clear_rect_black(frame_x + 2, frame_y + 8, MAP1_STORY_ENEMY_DRAW_W + 4, MAP1_STORY_ENEMY_DRAW_H + 4)
        map1_story_prev_flowey_visible = flowey_visible

        fire_present = (map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_FIRE_FLY or map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_FIRE_HOLD)
        if fire_present:
            map1_story_fire_prev_x = map1_story_fire_x
            map1_story_fire_prev_y = map1_story_fire_y
            map1_story_fire_prev_valid = True
        else:
            map1_story_fire_prev_valid = False

        if flowey_visible and hasattr(lgfx, "draw_png_file") and _path_exists(enemy_sprite_path):
            enemy_drawn = bool(
                lgfx.draw_png_file(
                    enemy_sprite_path,
                    enemy_x,
                    enemy_y,
                    enemy_sprite_w,
                    enemy_sprite_h,
                )
            )
        if flowey_visible and (not enemy_drawn):
            monster_cx = frame_x + (frame_w // 2)
            monster_cy = frame_y + 75
            lgfx.draw_circle(monster_cx, monster_cy, 22, BATTLE_COLOR_WHITE)
            enemy_x = monster_cx - 22
            enemy_y = monster_cy - 22
            enemy_sprite_w = 44
            enemy_sprite_h = 44
            enemy_bottom = monster_cy + 22
            enemy_drawn = True

        if fire_present:
            fire_path = _map1_story_fire_sprite_path()
            fire_drawn = False
            if hasattr(lgfx, "draw_png_file") and _path_exists(fire_path):
                fire_drawn = bool(
                    lgfx.draw_png_file(
                        fire_path,
                        map1_story_fire_x,
                        map1_story_fire_y,
                        MAP1_STORY_FIRE_DRAW_W,
                        MAP1_STORY_FIRE_DRAW_H,
                    )
                )
            if not fire_drawn:
                fire_cx = map1_story_fire_x + (MAP1_STORY_FIRE_DRAW_W // 2)
                fire_cy = map1_story_fire_y + (MAP1_STORY_FIRE_DRAW_H // 2)
                lgfx.draw_circle(fire_cx, fire_cy, 12, BATTLE_COLOR_WHITE)
                lgfx.draw_circle(fire_cx, fire_cy, 8, BATTLE_COLOR_RED)

        if map1_story_toriel_visible:
            toriel_path = _map1_story_toriel_sprite_path()
            toriel_drawn = False
            if hasattr(lgfx, "draw_png_file") and _path_exists(toriel_path):
                toriel_drawn = bool(
                    lgfx.draw_png_file(
                        toriel_path,
                        map1_story_toriel_x,
                        frame_y + 10,
                        MAP1_STORY_TORIEL_DRAW_W,
                        MAP1_STORY_TORIEL_DRAW_H,
                    )
                )
            if not toriel_drawn:
                _draw_rect_thick(
                    map1_story_toriel_x + 12,
                    frame_y + 16,
                    MAP1_STORY_TORIEL_DRAW_W - 24,
                    MAP1_STORY_TORIEL_DRAW_H - 20,
                    BATTLE_COLOR_WHITE,
                    2,
                )
            enemy_x = map1_story_toriel_x
            enemy_y = frame_y + 10
            enemy_sprite_w = MAP1_STORY_TORIEL_DRAW_W
            enemy_sprite_h = MAP1_STORY_TORIEL_DRAW_H
            enemy_bottom = enemy_y + enemy_sprite_h
            map1_story_toriel_prev_x = map1_story_toriel_x
            map1_story_toriel_prev_y = frame_y + 10
            map1_story_toriel_prev_valid = True
        elif not flowey_visible:
            enemy_x = frame_x + ((frame_w - MAP1_STORY_FIRE_DRAW_W) // 2)
            enemy_y = frame_y + 10
            enemy_sprite_w = MAP1_STORY_FIRE_DRAW_W
            enemy_sprite_h = MAP1_STORY_FIRE_DRAW_H
            enemy_bottom = enemy_y + enemy_sprite_h
            map1_story_toriel_prev_valid = False
        else:
            map1_story_toriel_prev_valid = False
    else:
        if hasattr(lgfx, "draw_png_file") and _path_exists(enemy_sprite_path):
            enemy_drawn = bool(
                lgfx.draw_png_file(
                    enemy_sprite_path,
                    enemy_x,
                    enemy_y,
                    enemy_sprite_w,
                    enemy_sprite_h,
                )
            )
        if not enemy_drawn:
            monster_cx = frame_x + (frame_w // 2)
            monster_cy = frame_y + 75
            lgfx.draw_circle(monster_cx, monster_cy, 22, BATTLE_COLOR_WHITE)
            enemy_x = monster_cx - 22
            enemy_y = monster_cy - 22
            enemy_sprite_w = 44
            enemy_sprite_h = 44
            enemy_bottom = monster_cy + 22
    battle_menu_enemy_x = enemy_x
    battle_menu_enemy_y = enemy_y
    battle_menu_enemy_w = enemy_sprite_w
    battle_menu_enemy_h = enemy_sprite_h

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


def _map1_story_phase2_event_is_moving():
    return (
        _map1_story_is_active()
        and (
            map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_FIRE_FLY
            or map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_TORIEL_SLIDE
        )
    )


def _draw_map1_story_phase2_overlay(frame_x, frame_y, frame_w):
    global battle_menu_enemy_x, battle_menu_enemy_y, battle_menu_enemy_w, battle_menu_enemy_h
    global map1_story_fire_prev_x, map1_story_fire_prev_y, map1_story_fire_prev_valid
    global map1_story_toriel_prev_x, map1_story_toriel_prev_y, map1_story_toriel_prev_valid, map1_story_prev_flowey_visible

    if not _map1_story_phase2_event_is_moving():
        return battle_menu_enemy_y + battle_menu_enemy_h

    fire_present = (
        map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_FIRE_FLY
        or map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_FIRE_HOLD
    )
    toriel_curr_y = frame_y + 10

    if map1_story_fire_prev_valid:
        clear_fire_curr_x = map1_story_fire_x if fire_present else (map1_story_fire_prev_x - (MAP1_STORY_FIRE_DRAW_W + 64))
        clear_fire_curr_y = map1_story_fire_y if fire_present else map1_story_fire_prev_y
        _clear_story_prev_delta(
            frame_x,
            frame_y,
            frame_w,
            map1_story_fire_prev_x,
            map1_story_fire_prev_y,
            clear_fire_curr_x,
            clear_fire_curr_y,
            MAP1_STORY_FIRE_DRAW_W,
            MAP1_STORY_FIRE_DRAW_H,
            pad=4,
            include_outside=False,
            overlap_strip=2,
        )
    if map1_story_toriel_prev_valid:
        clear_toriel_curr_x = map1_story_toriel_x if map1_story_toriel_visible else (map1_story_toriel_prev_x - (MAP1_STORY_TORIEL_DRAW_W + 64))
        _clear_story_prev_delta(
            frame_x,
            frame_y,
            frame_w,
            map1_story_toriel_prev_x,
            map1_story_toriel_prev_y,
            clear_toriel_curr_x,
            toriel_curr_y,
            MAP1_STORY_TORIEL_DRAW_W,
            MAP1_STORY_TORIEL_DRAW_H,
            pad=6,
            include_outside=False,
            overlap_strip=4,
        )
        # Toriel slides left only; scrub a narrow trailing band on the right side
        # to remove alpha-edge residue that can stack between frames.
        if clear_toriel_curr_x < map1_story_toriel_prev_x:
            trail_x0 = clear_toriel_curr_x + MAP1_STORY_TORIEL_DRAW_W - 2
            trail_x1 = map1_story_toriel_prev_x + MAP1_STORY_TORIEL_DRAW_W + 4
            if trail_x1 > trail_x0:
                _clear_rect_black_in_battle_interior(
                    frame_x,
                    frame_y,
                    frame_w,
                    trail_x0,
                    toriel_curr_y - 3,
                    trail_x1 - trail_x0,
                    MAP1_STORY_TORIEL_DRAW_H + 6,
                )

    enemy_sprite_path = _map1_story_enemy_sprite_path()
    flowey_x = frame_x + 4
    flowey_y = frame_y + 10
    flowey_visible = not map1_story_flowey_hidden
    if (not flowey_visible) and map1_story_prev_flowey_visible:
        _clear_rect_black_in_battle_interior(
            frame_x,
            frame_y,
            frame_w,
            flowey_x - 2,
            flowey_y - 2,
            MAP1_STORY_ENEMY_DRAW_W + 4,
            MAP1_STORY_ENEMY_DRAW_H + 4,
        )
    map1_story_prev_flowey_visible = flowey_visible

    if flowey_visible:
        drew_flowey = False
        if hasattr(lgfx, "draw_png_file") and _path_exists(enemy_sprite_path):
            drew_flowey = bool(
                lgfx.draw_png_file(
                    enemy_sprite_path,
                    flowey_x,
                    flowey_y,
                    MAP1_STORY_ENEMY_DRAW_W,
                    MAP1_STORY_ENEMY_DRAW_H,
                )
            )
        if not drew_flowey:
            monster_cx = flowey_x + (MAP1_STORY_ENEMY_DRAW_W // 2)
            monster_cy = flowey_y + (MAP1_STORY_ENEMY_DRAW_H // 2)
            lgfx.draw_circle(monster_cx, monster_cy, 22, BATTLE_COLOR_WHITE)
        battle_menu_enemy_x = flowey_x
        battle_menu_enemy_y = flowey_y
        battle_menu_enemy_w = MAP1_STORY_ENEMY_DRAW_W
        battle_menu_enemy_h = MAP1_STORY_ENEMY_DRAW_H

    if fire_present:
        _clear_story_curr_fringe(
            frame_x,
            frame_y,
            frame_w,
            map1_story_fire_x,
            map1_story_fire_y,
            MAP1_STORY_FIRE_DRAW_W,
            MAP1_STORY_FIRE_DRAW_H,
            fringe=2,
        )
        fire_path = _map1_story_fire_sprite_path()
        fire_drawn = False
        if hasattr(lgfx, "draw_png_file") and _path_exists(fire_path):
            fire_drawn = bool(
                lgfx.draw_png_file(
                    fire_path,
                    map1_story_fire_x,
                    map1_story_fire_y,
                    MAP1_STORY_FIRE_DRAW_W,
                    MAP1_STORY_FIRE_DRAW_H,
                )
            )
        if not fire_drawn:
            fire_cx = map1_story_fire_x + (MAP1_STORY_FIRE_DRAW_W // 2)
            fire_cy = map1_story_fire_y + (MAP1_STORY_FIRE_DRAW_H // 2)
            lgfx.draw_circle(fire_cx, fire_cy, 12, BATTLE_COLOR_WHITE)
            lgfx.draw_circle(fire_cx, fire_cy, 8, BATTLE_COLOR_RED)
        map1_story_fire_prev_x = map1_story_fire_x
        map1_story_fire_prev_y = map1_story_fire_y
        map1_story_fire_prev_valid = True
    else:
        map1_story_fire_prev_valid = False

    if map1_story_toriel_visible:
        _clear_story_curr_fringe(
            frame_x,
            frame_y,
            frame_w,
            map1_story_toriel_x,
            toriel_curr_y,
            MAP1_STORY_TORIEL_DRAW_W,
            MAP1_STORY_TORIEL_DRAW_H,
            fringe=3,
        )
        toriel_path = _map1_story_toriel_sprite_path()
        toriel_drawn = False
        if hasattr(lgfx, "draw_png_file") and _path_exists(toriel_path):
            toriel_drawn = bool(
                lgfx.draw_png_file(
                    toriel_path,
                    map1_story_toriel_x,
                    toriel_curr_y,
                    MAP1_STORY_TORIEL_DRAW_W,
                    MAP1_STORY_TORIEL_DRAW_H,
                )
            )
        if not toriel_drawn:
            _draw_rect_thick(
                map1_story_toriel_x + 12,
                toriel_curr_y + 6,
                MAP1_STORY_TORIEL_DRAW_W - 24,
                MAP1_STORY_TORIEL_DRAW_H - 20,
                BATTLE_COLOR_WHITE,
                2,
            )
        map1_story_toriel_prev_x = map1_story_toriel_x
        map1_story_toriel_prev_y = toriel_curr_y
        map1_story_toriel_prev_valid = True
        battle_menu_enemy_x = map1_story_toriel_x
        battle_menu_enemy_y = toriel_curr_y
        battle_menu_enemy_w = MAP1_STORY_TORIEL_DRAW_W
        battle_menu_enemy_h = MAP1_STORY_TORIEL_DRAW_H
    else:
        map1_story_toriel_prev_valid = False
        if not flowey_visible:
            battle_menu_enemy_x = frame_x + ((frame_w - MAP1_STORY_FIRE_DRAW_W) // 2)
            battle_menu_enemy_y = frame_y + 10
            battle_menu_enemy_w = MAP1_STORY_FIRE_DRAW_W
            battle_menu_enemy_h = MAP1_STORY_FIRE_DRAW_H

    return battle_menu_enemy_y + battle_menu_enemy_h


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
        return False
    text_drawn = _draw_png_in_box(
        png_info,
        text_x,
        y + 1,
        text_w,
        h - 2,
        preserve_aspect=True,
        allow_upscale=False,
    )
    return text_drawn


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

    if index < 0 or index >= len(inventory_items):
        return "No items"
    item = inventory_items[index]
    if not item:
        return "No items"
    if _is_weapon_item(item):
        return "%s cannot be used" % item.get("name", "Weapon")

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
        src_w, src_h = _battle_enemy_act_option_source_size(i)
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
    global battle_menu_enemy_x, battle_menu_enemy_y, battle_menu_enemy_w, battle_menu_enemy_h
    global map1_enemy_anchor_mode
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
        or (_map1_story_is_active() and map1_enemy_anchor_mode == MAP1_ENEMY_ANCHOR_SLIDING_LEFT)
    )
    moving_story = _map1_story_phase2_event_is_moving()
    if static_changed:
        if (not did_full_clear) and battle_menu_static_ready and (not moving_story):
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
    elif moving_story:
        battle_menu_enemy_bottom_used = _draw_map1_story_phase2_overlay(frame_x, frame_y, frame_w)

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
        if _map1_story_is_active():
            dialog_x, dialog_render_y, dialog_w, dialog_h = _map1_story_dialog_safe_rect(frame_x, frame_y, frame_w, cmd_y)
        else:
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
            option_entry = _battle_enemy_act_option_entry(i)
            option_png_info = _enemy_entry_png_info(option_entry)
            if option_png_info and _draw_star_line_with_png(option_png_info, slot[0], slot[1], slot[2], slot[3]):
                continue
            _draw_star_line_with_text(
                _enemy_entry_text(option_entry, "ACT"),
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

    rendered = False
    if battle_dialog_png_info:
        if _map1_story_is_active():
            rendered = _draw_png_in_box(
                battle_dialog_png_info,
                dialog_x,
                dialog_render_y,
                dialog_w,
                dialog_h,
                preserve_aspect=True,
                allow_upscale=False,
            )
        else:
            rendered = _draw_star_line_with_png(
                battle_dialog_png_info,
                dialog_x,
                dialog_render_y + ((dialog_h - 20) // 2),
                dialog_w,
                20,
            )
    if (not _map1_story_is_active()) and (not rendered) and battle_dialog_text:
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


def _draw_battle_heart_mask(cx, cy, color):
    # Stable pixel-heart style (single rendering path, no PNG decode jitter).
    # Spans are (y_offset, ((x0, x1), ...)) relative to heart center.
    body = (
        (-5, ((-2, -1), (1, 2))),
        (-4, ((-4, 4),)),
        (-3, ((-4, 4),)),
        (-2, ((-4, 4),)),
        (-1, ((-3, 3),)),
        (0, ((-3, 3),)),
        (1, ((-2, 2),)),
        (2, ((-1, 1),)),
        (3, ((0, 0),)),
    )
    shine = (
        (-4, ((-2, -2),)),
        (-3, ((-3, -3), (-1, -1))),
        (-2, ((-3, -3),)),
    )

    for y_off, spans in body:
        yy = cy + y_off
        for x0, x1 in spans:
            lgfx.draw_rect(cx + x0, yy, x1 - x0 + 1, 1, color)

    shine_color = 0xFD55  # light pink highlight
    for y_off, spans in shine:
        yy = cy + y_off
        for x0, x1 in spans:
            lgfx.draw_rect(cx + x0, yy, x1 - x0 + 1, 1, shine_color)


def _rand_u32():
    global _rng_state
    _rng_state = ((_rng_state * 1103515245) + 12345) & 0x7FFFFFFF
    return _rng_state


def _rand_range(lo, hi):
    if hi <= lo:
        return lo
    span = hi - lo + 1
    return lo + (_rand_u32() % span)


def _battle_enemy_profile():
    if current_battle_enemy:
        return current_battle_enemy
    return ENEMY_REGISTRY.get(DEFAULT_BATTLE_ENEMY_ID, {})


def _battle_enemy_resolve(enemy_id=None):
    if enemy_id:
        resolved = ENEMY_REGISTRY.get(enemy_id)
        if resolved:
            return resolved
    return ENEMY_REGISTRY.get(DEFAULT_BATTLE_ENEMY_ID, {})


def _set_current_battle_enemy(enemy_id=None):
    global current_battle_enemy
    current_battle_enemy = _battle_enemy_resolve(enemy_id)


def _enemy_entry_png_info(entry):
    if not entry:
        return None
    path = entry.get("png")
    if not path:
        return None
    resolved = _resolve_runtime_png_path(path)
    if resolved and resolved != path:
        entry["png"] = resolved
        path = resolved
    src_w = int(entry.get("png_w", 0))
    src_h = int(entry.get("png_h", 0))
    if src_w < 1:
        src_w = 120
    if src_h < 1:
        src_h = 18
    return (path, src_w, src_h)


def _enemy_entry_text(entry, fallback_text=""):
    if not entry:
        return fallback_text
    text = entry.get("text")
    if not text:
        return fallback_text
    return text


def _battle_enemy_sprite_info():
    profile = _battle_enemy_profile()
    path = profile.get("sprite_path", ENEMY_SPRITE_PATH)
    resolved = _resolve_runtime_png_path(path)
    if resolved and resolved != path:
        profile["sprite_path"] = resolved
        path = resolved
    draw_w = int(profile.get("sprite_w", ENEMY_SPRITE_W))
    draw_h = int(profile.get("sprite_h", ENEMY_SPRITE_H))
    if draw_w < 1:
        draw_w = ENEMY_SPRITE_W
    if draw_h < 1:
        draw_h = ENEMY_SPRITE_H
    return path, draw_w, draw_h


def _battle_enemy_display_name():
    if _map1_story_is_active():
        return "FLOWEY"
    profile = _battle_enemy_profile()
    return profile.get("display_name", MONSTER_NAME)


def _battle_enemy_act_option_entry(index):
    profile = _battle_enemy_profile()
    options = profile.get("act_options", ())
    if index >= 0 and index < len(options):
        entry = options[index]
        if entry:
            return entry
    fallback = ENEMY_REGISTRY.get(DEFAULT_BATTLE_ENEMY_ID, {}).get("act_options", ())
    if index >= 0 and index < len(fallback):
        return fallback[index]
    return {"text": "ACT"}


def _battle_enemy_act_reply_entry(index):
    profile = _battle_enemy_profile()
    replies = profile.get("act_replies", ())
    if index >= 0 and index < len(replies):
        entry = replies[index]
        if entry:
            return entry
    fallback = ENEMY_REGISTRY.get(DEFAULT_BATTLE_ENEMY_ID, {}).get("act_replies", ())
    if index >= 0 and index < len(fallback):
        return fallback[index]
    return {"text": "..."}


def _battle_enemy_mercy_locked_entry():
    profile = _battle_enemy_profile()
    entry = profile.get("mercy_locked")
    if entry:
        return entry
    return ENEMY_REGISTRY.get(DEFAULT_BATTLE_ENEMY_ID, {}).get("mercy_locked")


def _battle_enemy_mercy_success_entry():
    profile = _battle_enemy_profile()
    entry = profile.get("mercy_success")
    if entry:
        return entry
    return ENEMY_REGISTRY.get(DEFAULT_BATTLE_ENEMY_ID, {}).get("mercy_success")


def _battle_enemy_dialog_apply_entry(entry):
    global battle_dialog_png_info, battle_dialog_text
    battle_dialog_png_info = _enemy_entry_png_info(entry)
    text = _enemy_entry_text(entry, "")
    battle_dialog_text = text if text else None


def _battle_enemy_act_option_source_size(index):
    entry = _battle_enemy_act_option_entry(index)
    png_info = _enemy_entry_png_info(entry)
    if png_info:
        return png_info[1], png_info[2]
    text = _enemy_entry_text(entry, "ACT")
    text_w = len(text) * 8
    if text_w < 32:
        text_w = 32
    return text_w, 12


def _map1_story_is_active():
    return bool(map1_story_active and (current_map_id == MAP1_ID))


def _map1_story_is_toriel_lines():
    return bool(map1_story_line_index >= 10)


def _map1_story_fire_sprite_path():
    resolved = _resolve_first_existing_path(MAP1_FIRE_SPRITE_PATHS)
    if resolved:
        return resolved
    return MAP1_FIRE_SPRITE_PATHS[0]


def _map1_story_toriel_sprite_path():
    resolved = _resolve_first_existing_path(MAP1_TORIEL_SPRITE_PATHS)
    if resolved:
        return resolved
    return MAP1_TORIEL_SPRITE_PATHS[0]


def _map1_story_init_rescue_positions():
    global map1_story_fire_x, map1_story_fire_y, map1_story_fire_start_x, map1_story_fire_start_y
    global map1_story_fire_target_x, map1_story_fire_target_y
    global map1_story_toriel_x, map1_story_toriel_start_x, map1_story_toriel_target_x

    frame_w = BATTLE_FRAME_W
    frame_x, frame_y, _, _, _ = _battle_menu_geometry(frame_w)
    flowey_x = frame_x + 4
    flowey_y = frame_y + 10
    flowey_cx = flowey_x + (MAP1_STORY_ENEMY_DRAW_W // 2)
    flowey_cy = flowey_y + (MAP1_STORY_ENEMY_DRAW_H // 2)
    fire_y = flowey_y + ((MAP1_STORY_ENEMY_DRAW_H - MAP1_STORY_FIRE_DRAW_H) // 2)
    if fire_y < frame_y + 4:
        fire_y = frame_y + 4
    fire_start_x = frame_x + frame_w - MAP1_STORY_FIRE_DRAW_W - 6
    fire_target_x = flowey_cx - (MAP1_STORY_FIRE_DRAW_W // 2) - MAP1_STORY_FIRE_HIT_OVERLAP_PX
    fire_target_y = flowey_cy - (MAP1_STORY_FIRE_DRAW_H // 2)
    toriel_target_x = frame_x + frame_w - MAP1_STORY_TORIEL_DRAW_W - 8 - MAP1_STORY_TORIEL_TARGET_SHIFT_LEFT_PX
    if toriel_target_x < frame_x + 4:
        toriel_target_x = frame_x + 4
    # Start fully inside the battle frame (not from screen edge), then slide left.
    toriel_start_x = frame_x + frame_w - MAP1_STORY_TORIEL_DRAW_W
    map1_story_fire_x = fire_start_x
    map1_story_fire_y = fire_y
    map1_story_fire_start_x = fire_start_x
    map1_story_fire_start_y = fire_y
    map1_story_fire_target_x = fire_target_x
    map1_story_fire_target_y = fire_target_y
    map1_story_toriel_x = toriel_start_x
    map1_story_toriel_start_x = toriel_start_x
    map1_story_toriel_target_x = toriel_target_x


def _map1_story_begin_phase2_rescue(loop_start):
    global map1_story_phase2_event, map1_story_phase2_event_started_ms, map1_story_phase2_freeze_until_ms
    global battle_fight_dirty, battle_bullets_dirty

    if map1_story_phase2_event != MAP1_STORY_PHASE2_EVENT_NONE:
        return
    map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_PAUSE
    map1_story_phase2_event_started_ms = loop_start
    map1_story_phase2_freeze_until_ms = time.ticks_add(loop_start, MAP1_STORY_PHASE2_FREEZE_MS)
    battle_fight_dirty = False
    battle_bullets_dirty = False


def _map1_story_enter_phase2_rescue_menu(loop_start):
    global mode, bullets, battle_prev_bullet_positions, battle_bullets_dirty
    global battle_menu_dirty, battle_dialog_visible, battle_menu_full_clear_pending, battle_menu_static_ready, battle_menu_prev_dialog_active
    global battle_dialog_mode, battle_dialog_png_info, battle_dialog_text, act_dialog_until_ms
    global map1_story_phase2_event, map1_story_phase2_event_started_ms, map1_enemy_anchor_mode, map1_story_flowey_hidden, map1_story_toriel_visible
    global map1_story_fire_prev_valid, map1_story_toriel_prev_valid, map1_story_prev_flowey_visible

    mode = MODE_BATTLE_MENU
    bullets = []
    battle_prev_bullet_positions = []
    battle_bullets_dirty = False
    battle_menu_dirty = True
    battle_dialog_visible = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    battle_menu_prev_dialog_active = False
    battle_dialog_mode = BATTLE_DIALOG_NONE
    battle_dialog_png_info = None
    battle_dialog_text = None
    act_dialog_until_ms = 0
    map1_enemy_anchor_mode = MAP1_ENEMY_ANCHOR_LEFT
    map1_story_flowey_hidden = False
    map1_story_toriel_visible = False
    map1_story_fire_prev_valid = False
    map1_story_toriel_prev_valid = False
    map1_story_prev_flowey_visible = True
    _map1_story_init_rescue_positions()
    map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_FIRE_FLY
    map1_story_phase2_event_started_ms = loop_start


def _map1_story_begin_toriel_lines(loop_start):
    global map1_story_phase2_event, map1_story_phase2_event_started_ms
    global battle_menu_dirty, battle_menu_full_clear_pending, battle_menu_static_ready
    global map1_story_fire_prev_valid, map1_story_toriel_prev_valid

    map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_TORIEL_LINES
    map1_story_phase2_event_started_ms = loop_start
    map1_story_fire_prev_valid = False
    map1_story_toriel_prev_valid = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    _map1_story_show_line(10, loop_start)
    battle_menu_dirty = True


def _map1_story_reset():
    global map1_story_active, map1_story_stage, map1_story_line_index, map1_story_next_ms
    global map1_story_enemy_angry, map1_enemy_anchor_mode, map1_enemy_slide_start_ms
    global map1_story_phase2_center_x, map1_story_phase2_center_y
    global map1_story_phase2_event, map1_story_phase2_event_started_ms, map1_story_phase2_freeze_until_ms
    global map1_story_fire_x, map1_story_fire_y, map1_story_fire_start_x, map1_story_fire_start_y, map1_story_fire_target_x, map1_story_fire_target_y
    global map1_story_flowey_hidden, map1_story_toriel_visible, map1_story_toriel_x, map1_story_toriel_start_x, map1_story_toriel_target_x
    global map1_story_fire_prev_x, map1_story_fire_prev_y, map1_story_fire_prev_valid
    global map1_story_toriel_prev_x, map1_story_toriel_prev_y, map1_story_toriel_prev_valid, map1_story_prev_flowey_visible

    map1_story_active = False
    map1_story_stage = MAP1_STORY_STAGE_NONE
    map1_story_line_index = -1
    map1_story_next_ms = 0
    map1_story_enemy_angry = False
    map1_enemy_anchor_mode = MAP1_ENEMY_ANCHOR_CENTER
    map1_enemy_slide_start_ms = 0
    map1_story_phase2_center_x = 0
    map1_story_phase2_center_y = 0
    map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_NONE
    map1_story_phase2_event_started_ms = 0
    map1_story_phase2_freeze_until_ms = 0
    map1_story_fire_x = 0
    map1_story_fire_y = 0
    map1_story_fire_start_x = 0
    map1_story_fire_start_y = 0
    map1_story_fire_target_x = 0
    map1_story_fire_target_y = 0
    map1_story_flowey_hidden = False
    map1_story_toriel_visible = False
    map1_story_toriel_x = 0
    map1_story_toriel_start_x = 0
    map1_story_toriel_target_x = 0
    map1_story_fire_prev_x = 0
    map1_story_fire_prev_y = 0
    map1_story_fire_prev_valid = False
    map1_story_toriel_prev_x = 0
    map1_story_toriel_prev_y = 0
    map1_story_toriel_prev_valid = False
    map1_story_prev_flowey_visible = True


def _map1_story_enemy_sprite_path():
    paths = MAP1_ANGRY_FLOWEY_ANIM_SPRITE_PATHS if map1_story_enemy_angry else MAP1_FLOWEY_ANIM_SPRITE_PATHS
    resolved = _resolve_first_existing_path(paths)
    if resolved:
        return resolved
    return paths[0]


def _map1_story_dialog_png_info(index):
    if index < 0 or index >= len(MAP1_STORY_LINE_PNG_PATHS):
        return None
    paths = MAP1_STORY_LINE_PNG_PATHS[index]
    path = _resolve_first_existing_path(paths)
    if not path:
        path = paths[0]
    if index == 0:
        return (path, MAP1_STORY_LINE1_PNG_W, MAP1_STORY_LINE1_PNG_H)
    return (path, MAP1_STORY_LINE_PNG_W, MAP1_STORY_LINE_PNG_H)


def _map1_story_show_line(index, now_ms):
    global map1_story_line_index, map1_story_next_ms
    global battle_dialog_mode, battle_dialog_started_ms, battle_dialog_png_info, battle_dialog_text
    global act_dialog_until_ms, battle_menu_dirty
    global map1_enemy_anchor_mode, map1_enemy_slide_start_ms

    map1_story_line_index = index
    map1_story_next_ms = time.ticks_add(now_ms, MAP1_STORY_LINE_MS)
    battle_dialog_mode = BATTLE_DIALOG_ITEM_RESULT
    battle_dialog_started_ms = now_ms
    battle_dialog_png_info = _map1_story_dialog_png_info(index)
    battle_dialog_text = None
    act_dialog_until_ms = map1_story_next_ms
    if index == 0 and map1_enemy_anchor_mode == MAP1_ENEMY_ANCHOR_CENTER:
        # For line 1, place FLOWEY on the left immediately.
        map1_enemy_anchor_mode = MAP1_ENEMY_ANCHOR_LEFT
        map1_enemy_slide_start_ms = now_ms
    battle_menu_dirty = True


def _map1_story_set_bullet_velocity_toward(bullet, tx, ty):
    bx = bullet[0] >> BULLET_FP_SHIFT
    by = bullet[1] >> BULLET_FP_SHIFT
    dx = tx - bx
    dy = ty - by
    scale = abs(dx)
    if abs(dy) > scale:
        scale = abs(dy)
    if scale <= 0:
        bullet[2] = 0
        bullet[3] = 0
        return
    bullet[2] = (dx << BULLET_FP_SHIFT) // scale
    bullet[3] = (dy << BULLET_FP_SHIFT) // scale
    if bullet[2] == 0 and bullet[3] == 0:
        bullet[2] = 1 << BULLET_FP_SHIFT


def _map1_story_bullet_bounds():
    inner_inset = BATTLE_FRAME_BORDER_THICK
    if BATTLE_BORDER_THICK > inner_inset:
        inner_inset = BATTLE_BORDER_THICK
    min_x = battle_frame_x + inner_inset + BULLET_R
    max_x = battle_frame_x + BATTLE_FRAME_W - inner_inset - BULLET_R - 1
    min_y = battle_frame_y + inner_inset + BULLET_R
    max_y = battle_frame_y + BATTLE_FRAME_H - inner_inset - BULLET_R - 1
    return min_x, max_x, min_y, max_y


def _map1_story_spawn_phase1_bullets():
    global bullets

    min_x, max_x, min_y, max_y = _map1_story_bullet_bounds()
    mid_x = (min_x + max_x) // 2
    mid_y = (min_y + max_y) // 2
    points = (
        (mid_x, min_y),
        (min_x, mid_y),
        (max_x, mid_y),
        (min_x, min_y),
        (max_x, max_y),
    )
    bullets = []
    for sx, sy in points:
        b = [sx << BULLET_FP_SHIFT, sy << BULLET_FP_SHIFT, 0, 0]
        _map1_story_set_bullet_velocity_toward(b, fight_heart_x, fight_heart_y)
        bullets.append(b)


def _map1_story_spawn_phase2_bullets():
    global bullets, map1_story_phase2_center_x, map1_story_phase2_center_y

    min_x, max_x, min_y, max_y = _map1_story_bullet_bounds()
    cx = _clamp(fight_heart_x, min_x, max_x)
    cy = _clamp(fight_heart_y, min_y, max_y)
    map1_story_phase2_center_x = cx
    map1_story_phase2_center_y = cy
    ring_r = cx - min_x
    if (max_x - cx) < ring_r:
        ring_r = max_x - cx
    if (cy - min_y) < ring_r:
        ring_r = cy - min_y
    if (max_y - cy) < ring_r:
        ring_r = max_y - cy
    if ring_r < 20:
        ring_r = 20
    dirs = (
        (100, 0),
        (97, 26),
        (87, 50),
        (71, 71),
        (50, 87),
        (26, 97),
        (0, 100),
        (-26, 97),
        (-50, 87),
        (-71, 71),
        (-87, 50),
        (-97, 26),
        (-100, 0),
        (-97, -26),
        (-87, -50),
        (-71, -71),
        (-50, -87),
        (-26, -97),
        (0, -100),
        (26, -97),
        (50, -87),
        (71, -71),
        (87, -50),
        (97, -26),
    )
    bullets = []
    for dxp, dyp in dirs:
        sx = cx + ((ring_r * dxp) // 100)
        sy = cy + ((ring_r * dyp) // 100)
        sx = _clamp(sx, min_x, max_x)
        sy = _clamp(sy, min_y, max_y)
        b = [sx << BULLET_FP_SHIFT, sy << BULLET_FP_SHIFT, 0, 0]
        _map1_story_set_bullet_velocity_toward(b, cx, cy)
        bullets.append(b)


def _map1_story_begin_phase1(loop_start):
    global mode, map1_story_stage, battle_menu_dirty, battle_dialog_visible
    global battle_menu_full_clear_pending, battle_menu_static_ready, battle_menu_prev_dialog_active
    global battle_dialog_mode, battle_dialog_png_info, battle_dialog_text, act_dialog_until_ms
    global battle_fight_dirty, battle_bullets_dirty

    map1_story_stage = MAP1_STORY_STAGE_PHASE1
    mode = MODE_BATTLE_FIGHT
    battle_menu_dirty = True
    battle_dialog_visible = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    battle_menu_prev_dialog_active = False
    battle_dialog_mode = BATTLE_DIALOG_NONE
    battle_dialog_png_info = None
    battle_dialog_text = None
    act_dialog_until_ms = 0
    _reset_battle_state()
    _map1_story_spawn_phase1_bullets()
    battle_fight_dirty = True
    battle_bullets_dirty = True


def _map1_story_begin_phase2(loop_start):
    global mode, map1_story_stage, battle_menu_dirty, battle_dialog_visible
    global battle_menu_full_clear_pending, battle_menu_static_ready, battle_menu_prev_dialog_active
    global battle_dialog_mode, battle_dialog_png_info, battle_dialog_text, act_dialog_until_ms
    global battle_fight_dirty, battle_bullets_dirty
    global map1_story_phase2_event, map1_story_phase2_event_started_ms, map1_story_phase2_freeze_until_ms
    global map1_story_flowey_hidden, map1_story_toriel_visible

    map1_story_stage = MAP1_STORY_STAGE_PHASE2
    mode = MODE_BATTLE_FIGHT
    battle_menu_dirty = True
    battle_dialog_visible = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    battle_menu_prev_dialog_active = False
    battle_dialog_mode = BATTLE_DIALOG_NONE
    battle_dialog_png_info = None
    battle_dialog_text = None
    act_dialog_until_ms = 0
    map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_NONE
    map1_story_phase2_event_started_ms = 0
    map1_story_phase2_freeze_until_ms = 0
    map1_story_flowey_hidden = False
    map1_story_toriel_visible = False
    _reset_battle_state()
    _map1_story_spawn_phase2_bullets()
    battle_fight_dirty = True
    battle_bullets_dirty = True


def _map1_story_begin_stage_lines(loop_start, stage):
    global map1_story_stage
    map1_story_stage = stage
    if stage == MAP1_STORY_STAGE_INTRO_LINES:
        _map1_story_show_line(0, loop_start)
    else:
        _map1_story_show_line(6, loop_start)


def _map1_story_begin(loop_start):
    global map1_story_active, map1_story_enemy_angry, map1_enemy_anchor_mode

    _map1_story_reset()
    map1_story_active = True
    map1_story_enemy_angry = False
    map1_enemy_anchor_mode = MAP1_ENEMY_ANCHOR_CENTER
    _map1_story_begin_stage_lines(loop_start, MAP1_STORY_STAGE_INTRO_LINES)


def _map1_story_update_menu(loop_start):
    global map1_story_phase2_event, map1_story_phase2_event_started_ms
    global map1_story_fire_x, map1_story_fire_y
    global map1_story_flowey_hidden, map1_story_toriel_visible, map1_story_toriel_x
    global battle_menu_dirty, battle_menu_static_ready, battle_menu_full_clear_pending
    global enemy_hp

    if map1_story_stage == MAP1_STORY_STAGE_INTRO_LINES:
        if time.ticks_diff(loop_start, map1_story_next_ms) < 0:
            return
        if map1_story_line_index < 5:
            _map1_story_show_line(map1_story_line_index + 1, loop_start)
            return
        _map1_story_begin_phase1(loop_start)
        return
    if map1_story_stage == MAP1_STORY_STAGE_MID_LINES:
        if time.ticks_diff(loop_start, map1_story_next_ms) < 0:
            return
        if map1_story_line_index < 9:
            _map1_story_show_line(map1_story_line_index + 1, loop_start)
            return
        _map1_story_begin_phase2(loop_start)
        return
    if map1_story_stage == MAP1_STORY_STAGE_PHASE2:
        frame_x, frame_y, _, _, _ = _battle_menu_geometry(BATTLE_FRAME_W)
        if map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_FIRE_FLY:
            flowey_x = frame_x + 4
            flowey_y = frame_y + 10
            flowey_left = flowey_x
            flowey_top = flowey_y
            flowey_right = flowey_x + MAP1_STORY_ENEMY_DRAW_W
            flowey_bottom = flowey_y + MAP1_STORY_ENEMY_DRAW_H
            flowey_right_hit = flowey_right - MAP1_STORY_FLOWEY_HIT_CONFIRM_LEFT_PX
            if flowey_right_hit <= flowey_left:
                flowey_right_hit = flowey_left + 1
            hit_now = not (
                (map1_story_fire_x + MAP1_STORY_FIRE_DRAW_W) < flowey_left
                or map1_story_fire_x > flowey_right_hit
                or (map1_story_fire_y + MAP1_STORY_FIRE_DRAW_H) < flowey_top
                or map1_story_fire_y > flowey_bottom
            )
            if hit_now:
                map1_story_flowey_hidden = True
                enemy_hp = 0
                map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_FIRE_HOLD
                map1_story_phase2_event_started_ms = loop_start
                battle_menu_full_clear_pending = True
                battle_menu_static_ready = False
                battle_menu_dirty = True
                return

            dx = map1_story_fire_target_x - map1_story_fire_x
            dy = map1_story_fire_target_y - map1_story_fire_y
            sx = MAP1_STORY_FIRE_STEP_PX
            sy = MAP1_STORY_FIRE_STEP_PX
            if abs(dx) <= sx and abs(dy) <= sy:
                map1_story_fire_x = map1_story_fire_target_x
                map1_story_fire_y = map1_story_fire_target_y
                map1_story_flowey_hidden = True
                enemy_hp = 0
                map1_story_phase2_event = MAP1_STORY_PHASE2_EVENT_FIRE_HOLD
                map1_story_phase2_event_started_ms = loop_start
                battle_menu_full_clear_pending = True
                battle_menu_static_ready = False
            else:
                if dx > 0:
                    map1_story_fire_x += sx if dx > sx else dx
                elif dx < 0:
                    map1_story_fire_x -= sx if (-dx) > sx else (-dx)
                if dy > 0:
                    map1_story_fire_y += sy if dy > sy else dy
                elif dy < 0:
                    map1_story_fire_y -= sy if (-dy) > sy else (-dy)
            battle_menu_dirty = True
            return
        if map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_FIRE_HOLD:
            if time.ticks_diff(loop_start, map1_story_phase2_event_started_ms) >= MAP1_STORY_FIRE_HOLD_MS:
                map1_story_toriel_x = map1_story_toriel_target_x
                map1_story_phase2_event_started_ms = loop_start
                map1_story_toriel_visible = True
                _map1_story_begin_toriel_lines(loop_start)
            return
        if map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_TORIEL_LINES:
            if time.ticks_diff(loop_start, map1_story_next_ms) < 0:
                return
            if map1_story_line_index < 17:
                _map1_story_show_line(map1_story_line_index + 1, loop_start)
                return
            _exit_battle_to_explore()


def _map1_story_finish_phase1_hit(loop_start):
    global mode, bullets, map1_story_enemy_angry, map1_story_stage
    global battle_menu_dirty, battle_dialog_visible, battle_menu_full_clear_pending
    global battle_menu_static_ready, battle_menu_prev_dialog_active
    global battle_prev_bullet_positions, battle_bullets_dirty

    bullets = []
    battle_prev_bullet_positions = []
    battle_bullets_dirty = False
    map1_story_enemy_angry = True
    mode = MODE_BATTLE_MENU
    battle_menu_dirty = True
    battle_dialog_visible = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    battle_menu_prev_dialog_active = False
    map1_story_stage = MAP1_STORY_STAGE_MID_LINES
    _map1_story_show_line(6, loop_start)


def _map1_story_update_fight(loop_start):
    global fight_heart_x, fight_heart_y
    global bullets, battle_bullets_dirty, battle_fight_dirty, battle_status_dirty
    global player_hp

    if map1_story_stage == MAP1_STORY_STAGE_PHASE2 and map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_PAUSE:
        if time.ticks_diff(loop_start, map1_story_phase2_freeze_until_ms) >= 0:
            _map1_story_enter_phase2_rescue_menu(loop_start)
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

    hit_r = BATTLE_HEART_HIT_R + BULLET_R
    hit_r2 = hit_r * hit_r
    near_r = hit_r + MAP1_STORY_PHASE2_NEAR_HIT_PAD_PX
    near_r2 = near_r * near_r
    min_x, max_x, min_y, max_y = _map1_story_bullet_bounds()
    kept = []
    changed = False

    for b in bullets:
        if map1_story_stage == MAP1_STORY_STAGE_PHASE1:
            _map1_story_set_bullet_velocity_toward(b, fight_heart_x, fight_heart_y)
            speed = MAP1_STORY_PHASE1_BULLET_SPEED_PX
        else:
            speed = MAP1_STORY_PHASE2_BULLET_SPEED_PX
        b[0] += b[2] * speed
        b[1] += b[3] * speed
        bx = b[0] >> BULLET_FP_SHIFT
        by = b[1] >> BULLET_FP_SHIFT
        if bx < min_x or bx > max_x or by < min_y or by > max_y:
            changed = True
            continue
        dx = bx - fight_heart_x
        dy = by - fight_heart_y
        if map1_story_stage == MAP1_STORY_STAGE_PHASE2 and map1_story_phase2_event == MAP1_STORY_PHASE2_EVENT_NONE:
            if (dx * dx + dy * dy) <= near_r2:
                _map1_story_begin_phase2_rescue(loop_start)
                battle_bullets_dirty = bool(bullets)
                return
        if (dx * dx + dy * dy) <= hit_r2:
            if map1_story_stage == MAP1_STORY_STAGE_PHASE1:
                player_hp = 1
                battle_status_dirty = True
                _map1_story_finish_phase1_hit(loop_start)
                return
            if map1_story_stage == MAP1_STORY_STAGE_PHASE2:
                _map1_story_begin_phase2_rescue(loop_start)
                battle_bullets_dirty = bool(bullets)
                return
            _exit_battle_to_explore()
            return
        kept.append(b)
        changed = True

    if len(kept) != len(bullets):
        changed = True
    bullets = kept
    if not bullets:
        if map1_story_stage == MAP1_STORY_STAGE_PHASE1:
            _map1_story_spawn_phase1_bullets()
            changed = True
        elif map1_story_stage == MAP1_STORY_STAGE_PHASE2:
            _map1_story_spawn_phase2_bullets()
            changed = True
    battle_bullets_dirty = changed or bool(bullets)
    battle_fight_dirty = False


def _encounter_state_for_map(map_id):
    state = map_encounter_state.get(map_id)
    if state is None:
        state = {
            "rolled_quota": None,
            "remaining": 0,
            "cleared": False,
            "enemy_cursor": 0,
            "entry_travel_px": 0,
            "entry_ready_after_ms": 0,
        }
        map_encounter_state[map_id] = state
    return state


def _encounter_config_for_map(map_id):
    config = MAP_ENCOUNTER_CONFIG.get(map_id)
    if not config:
        return None
    if not config.get("enabled"):
        return None
    return config


def _encounter_roll_quota_once(map_id):
    config = _encounter_config_for_map(map_id)
    if not config:
        return
    state = _encounter_state_for_map(map_id)
    if state.get("rolled_quota") is not None:
        return
    quota_lo, quota_hi = config.get("quota_range", (0, 0))
    quota = _rand_range(quota_lo, quota_hi)
    if quota < 0:
        quota = 0
    state["rolled_quota"] = quota
    state["remaining"] = quota
    state["cleared"] = quota <= 0
    print("encounter_quota_roll:", map_id, quota)


def _encounter_on_map_enter(map_id):
    state = _encounter_state_for_map(map_id)
    state["entry_travel_px"] = 0
    entry_grace_ms = _rand_range(MAP_ENCOUNTER_ENTRY_GRACE_MIN_MS, MAP_ENCOUNTER_ENTRY_GRACE_MAX_MS)
    state["entry_ready_after_ms"] = time.ticks_add(time.ticks_ms(), entry_grace_ms)
    _encounter_roll_quota_once(map_id)


def _encounter_note_travel(map_id, travel_px):
    if travel_px <= 0:
        return
    config = _encounter_config_for_map(map_id)
    if not config:
        return
    state = _encounter_state_for_map(map_id)
    state["entry_travel_px"] = int(state.get("entry_travel_px", 0)) + int(travel_px)


def _encounter_entry_ready(map_id):
    config = _encounter_config_for_map(map_id)
    if not config:
        return True
    state = _encounter_state_for_map(map_id)
    ready_after_ms = int(state.get("entry_ready_after_ms", 0))
    if ready_after_ms and time.ticks_diff(time.ticks_ms(), ready_after_ms) < 0:
        return False
    return int(state.get("entry_travel_px", 0)) >= MAP_ENCOUNTER_ENTRY_MIN_TRAVEL_PX


def _encounter_in_portal_safe_zone(map_id, px, py):
    del map_id, px, py
    return False


def _encounter_pick_enemy_id(map_id):
    config = _encounter_config_for_map(map_id)
    if not config:
        return None
    enemy_ids = config.get("enemy_ids", ())
    if not enemy_ids:
        return None
    state = _encounter_state_for_map(map_id)
    pick_mode = config.get("pick_mode", MAP_ENCOUNTER_PICK_MODE_ROUND_ROBIN)
    if pick_mode != MAP_ENCOUNTER_PICK_MODE_ROUND_ROBIN:
        pick_mode = MAP_ENCOUNTER_PICK_MODE_ROUND_ROBIN
    cursor = int(state.get("enemy_cursor", 0))
    enemy_index = cursor % len(enemy_ids)
    state["enemy_cursor"] = cursor + 1
    return enemy_ids[enemy_index]


def _encounter_try_start(map_id, px, py):
    config = _encounter_config_for_map(map_id)
    if not config:
        return None
    _encounter_roll_quota_once(map_id)
    state = _encounter_state_for_map(map_id)
    if state.get("cleared"):
        return None
    if int(state.get("remaining", 0)) <= 0:
        state["remaining"] = 0
        state["cleared"] = True
        return None
    if not _encounter_entry_ready(map_id):
        return None
    if _encounter_in_portal_safe_zone(map_id, px, py):
        return None
    enemy_id = _encounter_pick_enemy_id(map_id)
    if not enemy_id:
        return None
    state["remaining"] = int(state.get("remaining", 0)) - 1
    if state["remaining"] <= 0:
        state["remaining"] = 0
        state["cleared"] = True
        print("encounter_map_cleared:", map_id)
    print("encounter_pick:", map_id, enemy_id, "remaining", state["remaining"])
    return enemy_id


def _battle_status_y():
    y = battle_frame_y + BATTLE_FRAME_H + 4
    max_y = ACTIVE_VIEW_H - 9
    if y > max_y:
        y = max_y
    return y


def _battle_status_y_menu():
    return battle_cmd_y - (8 + BATTLE_STATUS_TO_CMD_GAP)


def _reset_attack_state():
    global attack_started_ms, attack_cursor_x, attack_cursor_dir, attack_locked, battle_attack_dirty
    global attack_prev_cursor_draw_x

    attack_started_ms = 0
    attack_cursor_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_BAR_W) // 2)
    attack_cursor_dir = 1
    attack_locked = False
    battle_attack_dirty = True
    attack_prev_cursor_draw_x = -9999


def _reset_battle_state():
    global bullets, next_bullet_spawn_ms, damage_invuln_until_ms
    global battle_bullets_dirty, battle_prev_bullet_positions, battle_status_dirty
    global fight_heart_x, fight_heart_y, battle_prev_heart_x, battle_prev_heart_y
    global battle_heart_needs_sprite_refresh

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
    battle_heart_needs_sprite_refresh = False
    _reset_attack_state()


def _exit_battle_to_explore():
    global mode, encounter_cooldown_frames, mercy_exit_pending, map6_boss_battle_active
    global explore_force_full_redraw
    global battle_menu_dirty, battle_dialog_visible
    global battle_menu_full_clear_pending, battle_menu_static_ready, battle_menu_prev_dialog_active

    mode = MODE_EXPLORE
    encounter_cooldown_frames = ENCOUNTER_COOLDOWN_FRAMES
    _clear_act_dialog_state(True)
    mercy_exit_pending = False
    explore_force_full_redraw = True
    battle_menu_dirty = True
    battle_dialog_visible = False
    battle_menu_full_clear_pending = True
    battle_menu_static_ready = False
    battle_menu_prev_dialog_active = False
    _map1_story_reset()
    _reset_battle_state()
    map6_boss_battle_active = False


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


def _start_battle_from_explore(enemy_id=None):
    global mode, mercy_exit_pending, enemy_hp
    global battle_menu_dirty, battle_dialog_visible
    global battle_menu_full_clear_pending
    global battle_menu_static_ready, battle_menu_prev_dialog_active
    global explore_moved, explore_scrolled, explore_anim_changed
    global lamp_dialog_until_ms, explore_overlay_dirty
    global map6_boss_battle_active

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
    map6_boss_battle_active = enemy_id == "MAP6_BOSS"
    _set_current_battle_enemy(enemy_id)
    enemy_hp = ENEMY_HP_MAX
    _reset_battle_state()
    if current_map_id == MAP1_ID and (not map1_opening_battle_done):
        _map1_story_begin(time.ticks_ms())
    else:
        _map1_story_reset()
    print("battle_menu: Fight(GPIO38) Act(GPIO39) Item(GPIO40) Mercy(GPIO41)")
    explore_moved = False
    explore_scrolled = False
    explore_anim_changed = False


def _draw_battle_status_line(in_menu=False):
    if not hasattr(lgfx, "draw_text"):
        return
    name_text = _battle_enemy_display_name()
    hp_text = "HP"
    right_text = "%2d/%d" % (player_hp, PLAYER_HP_MAX)
    x = battle_frame_x + 12
    if in_menu:
        x = menu_frame_x_used + 12
        y = menu_cmd_y_used - (8 + BATTLE_STATUS_TO_CMD_GAP)
    else:
        y = _battle_status_y()

    if in_menu:
        # Show compact enemy HP above the monster name only in battle menu.
        enemy_bar_w = BATTLE_HP_BAR_W
        enemy_bar_h = BATTLE_HP_BAR_H
        enemy_bar_x = x
        enemy_bar_y = y - enemy_bar_h - 3
        enemy_status_text = "%d/%d" % (_clamp(enemy_hp, 0, ENEMY_HP_MAX), ENEMY_HP_MAX)
        enemy_status_x = enemy_bar_x + enemy_bar_w + 6
        enemy_status_y = enemy_bar_y - 1
        _draw_rect_thick(enemy_bar_x, enemy_bar_y, enemy_bar_w, enemy_bar_h, BATTLE_COLOR_WHITE, 1)
        enemy_inner_x = enemy_bar_x + 1
        enemy_inner_y = enemy_bar_y + 1
        enemy_inner_w = enemy_bar_w - 2
        enemy_inner_h = enemy_bar_h - 2
        if enemy_inner_w > 0 and enemy_inner_h > 0:
            _fill_rect_solid(enemy_inner_x, enemy_inner_y, enemy_inner_w, enemy_inner_h, ENEMY_HP_BAR_EMPTY_COLOR)
            enemy_now = _clamp(enemy_hp, 0, ENEMY_HP_MAX)
            enemy_fill_w = 0
            if ENEMY_HP_MAX > 0:
                enemy_fill_w = (enemy_inner_w * enemy_now) // ENEMY_HP_MAX
            if enemy_fill_w > 0:
                _fill_rect_solid(enemy_inner_x, enemy_inner_y, enemy_fill_w, enemy_inner_h, ENEMY_HP_BAR_FILL_COLOR)

    def _draw_bold_text(tx, ty, text):
        # Simulate a slightly larger/bolder look using 2x2 overdraw.
        lgfx.draw_text(tx, ty, text, BATTLE_COLOR_WHITE)
        lgfx.draw_text(tx + 1, ty, text, BATTLE_COLOR_WHITE)
        lgfx.draw_text(tx, ty + 1, text, BATTLE_COLOR_WHITE)
        lgfx.draw_text(tx + 1, ty + 1, text, BATTLE_COLOR_WHITE)

    if in_menu:
        _draw_bold_text(enemy_status_x, enemy_status_y, enemy_status_text)

    _draw_bold_text(x, y, name_text)
    bar_y = y + ((8 - BATTLE_HP_BAR_H) // 2)
    if bar_y < y:
        bar_y = y
    hp_w = len(hp_text) * 8
    bar_w = BATTLE_HP_BAR_W
    bar_h = BATTLE_HP_BAR_H

    if in_menu and _map1_story_is_active():
        # Keep player HP cluster on the right side during MAP1 story battle.
        right_w = len(right_text) * 8
        right_x = (menu_frame_x_used + menu_frame_w_used) - 10 - right_w
        bar_x = right_x - BATTLE_HP_BAR_GAP - bar_w
        hp_x = bar_x - BATTLE_HP_BAR_GAP - hp_w
        _draw_bold_text(hp_x, y, hp_text)
    else:
        name_w = len(name_text) * 8
        hp_x = x + name_w + BATTLE_HP_NAME_TO_HP_GAP
        _draw_bold_text(hp_x, y, hp_text)
        bar_x = hp_x + hp_w + BATTLE_HP_BAR_GAP

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

    if not (in_menu and _map1_story_is_active()):
        right_x = bar_x + bar_w + BATTLE_HP_BAR_GAP
    _draw_bold_text(right_x, y, right_text)


def _clear_battle_status_line_menu():
    y = menu_cmd_y_used - (8 + BATTLE_STATUS_TO_CMD_GAP)
    x = menu_frame_x_used + 8
    w = menu_frame_w_used - 16
    clear_y = y - BATTLE_HP_BAR_H - 3
    # Clear both enemy HP bar band and status text; never overlap command button row.
    h = 10 + BATTLE_HP_BAR_H + 3
    max_h = menu_cmd_y_used - y - 1
    if max_h < 1:
        return
    if h > (max_h + BATTLE_HP_BAR_H + 3):
        h = max_h + BATTLE_HP_BAR_H + 3
    _clear_rect_black(x, clear_y, w, h)


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


def _attack_capsule_row_span(x, y, w, h, yy):
    if yy < y or yy >= y + h:
        return None
    r = h // 2
    if r < 1 or w <= h:
        return x, x + w - 1

    cy = y + r
    dy = yy - cy
    if dy < 0:
        dy = -dy
    v = (r * r) - (dy * dy)
    if v < 0:
        v = 0
    dx = int(v ** 0.5)

    left_cx = x + r
    right_cx = x + w - r - 1
    return left_cx - dx, right_cx + dx


def _draw_attack_capsule_fill(x, y, w, h, color, clip_x0=None, clip_x1=None):
    if w <= 0 or h <= 0:
        return
    for yy in range(y, y + h):
        span = _attack_capsule_row_span(x, y, w, h, yy)
        if not span:
            continue
        left, right = span
        if clip_x0 is not None and left < clip_x0:
            left = clip_x0
        if clip_x1 is not None and right > clip_x1:
            right = clip_x1
        if right >= left:
            _fill_rect_solid(left, yy, right - left + 1, 1, color)


def _draw_attack_capsule_outline(x, y, w, h, color, clip_x0=None, clip_x1=None):
    if w <= 0 or h <= 0:
        return
    for yy in range(y, y + h):
        span = _attack_capsule_row_span(x, y, w, h, yy)
        if not span:
            continue
        left, right = span
        if clip_x0 is not None and left < clip_x0 and right < clip_x0:
            continue
        if clip_x1 is not None and left > clip_x1 and right > clip_x1:
            continue
        if clip_x0 is None or left >= clip_x0:
            if clip_x1 is None or left <= clip_x1:
                lgfx.draw_rect(left, yy, 1, 1, color)
        if right != left:
            if clip_x0 is None or right >= clip_x0:
                if clip_x1 is None or right <= clip_x1:
                    lgfx.draw_rect(right, yy, 1, 1, color)


def _draw_attack_capsule_ring(x, y, w, h, ring_color, fill_color, clip_x0=None, clip_x1=None):
    _draw_attack_capsule_fill(x, y, w, h, ring_color, clip_x0, clip_x1)
    if w > 2 and h > 2:
        _draw_attack_capsule_fill(x + 1, y + 1, w - 2, h - 2, fill_color, clip_x0, clip_x1)


def _draw_attack_zone_overlays(x, y, w, h, low_w, perfect_w, clip_x0=None, clip_x1=None):
    right_x = x + w - 1
    left_low_end = x + low_w - 1
    right_low_start = right_x - low_w + 1
    perfect_x = x + ((w - perfect_w) // 2)
    perfect_end = perfect_x + perfect_w - 1

    zone_clip_x0 = clip_x0 if clip_x0 is not None else x
    zone_clip_x1 = clip_x1 if clip_x1 is not None else right_x

    if low_w > 0:
        left_clip_x0 = zone_clip_x0 if zone_clip_x0 > x else x
        left_clip_x1 = zone_clip_x1 if zone_clip_x1 < left_low_end else left_low_end
        if left_clip_x1 >= left_clip_x0:
            _draw_attack_capsule_fill(x, y, w, h, ATTACK_BAR_LOW_ZONE_COLOR, left_clip_x0, left_clip_x1)

        right_clip_x0 = zone_clip_x0 if zone_clip_x0 > right_low_start else right_low_start
        right_clip_x1 = zone_clip_x1 if zone_clip_x1 < right_x else right_x
        if right_clip_x1 >= right_clip_x0:
            _draw_attack_capsule_fill(x, y, w, h, ATTACK_BAR_LOW_ZONE_COLOR, right_clip_x0, right_clip_x1)
    if perfect_w > 0:
        perfect_clip_x0 = zone_clip_x0 if zone_clip_x0 > perfect_x else perfect_x
        perfect_clip_x1 = zone_clip_x1 if zone_clip_x1 < perfect_end else perfect_end
        _draw_attack_capsule_fill(
            x,
            y,
            w,
            h,
            ATTACK_BAR_PERFECT_COLOR,
            perfect_clip_x0,
            perfect_clip_x1,
        )
        core_w = perfect_w - 6
        if core_w > 1:
            core_x = perfect_x + ((perfect_w - core_w) // 2)
            core_end = core_x + core_w - 1
            core_clip_x0 = zone_clip_x0 if zone_clip_x0 > core_x else core_x
            core_clip_x1 = zone_clip_x1 if zone_clip_x1 < core_end else core_end
            _draw_attack_capsule_fill(
                x,
                y,
                w,
                h,
                ATTACK_BAR_PERFECT_CORE_COLOR,
                core_clip_x0,
                core_clip_x1,
            )

    tick_positions = (
        perfect_x - 5,
        perfect_x - 2,
        perfect_end + 2,
        perfect_end + 5,
    )
    for tx in tick_positions:
        if tx < x or tx > right_x:
            continue
        if clip_x0 is not None and tx < clip_x0:
            continue
        if clip_x1 is not None and tx > clip_x1:
            continue
        _draw_attack_capsule_fill(tx, y, 1, h, ATTACK_BAR_TICK_COLOR)

    return perfect_x, perfect_end


def _draw_attack_pixel_noise(x, y, w, h, skip_x0, skip_x1, clip_x0=None, clip_x1=None):
    if w < 10 or h < 4:
        return

    row_offsets = (1, 3, h - 4, h - 2)
    seg_len = 4
    step = 14

    for row_i, row_off in enumerate(row_offsets):
        yy = y + row_off
        if yy < y or yy >= y + h:
            continue
        span = _attack_capsule_row_span(x, y, w, h, yy)
        if not span:
            continue
        left_span, right_span = span
        px = left_span + 4
        while px + seg_len - 1 <= right_span - 4:
            seg_x0 = px
            seg_x1 = px + seg_len - 1
            if clip_x0 is not None and seg_x1 < clip_x0:
                px += step
                continue
            if clip_x1 is not None and seg_x0 > clip_x1:
                break
            if seg_x1 < skip_x0 or seg_x0 > skip_x1:
                # Use absolute segment coordinate so clipped partial redraws are deterministic.
                seg_i = (seg_x0 - x) // step
                color = ATTACK_BAR_DECOR_RED if ((seg_i + row_i) & 1) == 0 else ATTACK_BAR_DECOR_YELLOW
                draw_x0 = seg_x0
                draw_x1 = seg_x1
                if clip_x0 is not None and draw_x0 < clip_x0:
                    draw_x0 = clip_x0
                if clip_x1 is not None and draw_x1 > clip_x1:
                    draw_x1 = clip_x1
                if draw_x1 >= draw_x0:
                    _fill_rect_solid(draw_x0, yy, draw_x1 - draw_x0 + 1, 1, color)
            px += step


def _draw_attack_bar_static_layers(bar_x, bar_y, clip_x0=None, clip_x1=None):
    inner_x = bar_x + 1
    inner_y = bar_y + 1
    inner_w = ATTACK_BAR_W - 2
    inner_h = ATTACK_BAR_H - 2
    if inner_w <= 0 or inner_h <= 0:
        return

    good_w = (inner_w * ATTACK_ZONE_GOOD_PCT) // 100
    if good_w < 1:
        good_w = 1
    if good_w > inner_w:
        good_w = inner_w

    perfect_w = (inner_w * ATTACK_ZONE_PERFECT_PCT) // 100
    if perfect_w < 1:
        perfect_w = 1
    if perfect_w > good_w:
        perfect_w = good_w

    low_w = (inner_w - good_w) // 2
    if low_w < 0:
        low_w = 0

    fill_clip_x0 = clip_x0
    fill_clip_x1 = clip_x1
    if fill_clip_x0 is None:
        fill_clip_x0 = inner_x
    if fill_clip_x1 is None:
        fill_clip_x1 = inner_x + inner_w - 1
    _draw_attack_capsule_ring(
        bar_x - 2,
        bar_y - 2,
        ATTACK_BAR_W + 4,
        ATTACK_BAR_H + 4,
        ATTACK_BAR_OUTLINE_COLOR,
        ATTACK_BAR_BORDER_COLOR,
        clip_x0,
        clip_x1,
    )
    _draw_attack_capsule_ring(
        bar_x - 1,
        bar_y - 1,
        ATTACK_BAR_W + 2,
        ATTACK_BAR_H + 2,
        ATTACK_BAR_BORDER_COLOR,
        ATTACK_BAR_BG_COLOR,
        clip_x0,
        clip_x1,
    )
    _draw_attack_capsule_fill(inner_x, inner_y, inner_w, inner_h, ATTACK_BAR_BG_COLOR, fill_clip_x0, fill_clip_x1)
    perfect_x, perfect_end = _draw_attack_zone_overlays(inner_x, inner_y, inner_w, inner_h, low_w, perfect_w, fill_clip_x0, fill_clip_x1)
    _draw_attack_pixel_noise(inner_x, inner_y, inner_w, inner_h, perfect_x, perfect_end, fill_clip_x0, fill_clip_x1)
    _draw_attack_capsule_outline(inner_x, inner_y, inner_w, inner_h, ATTACK_BAR_BORDER_INNER_COLOR, clip_x0, clip_x1)


def draw_battle_attack_screen(full_refresh=False):
    global attack_prev_cursor_draw_x

    bar_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_BAR_W) // 2)
    bar_y = battle_frame_y + (BATTLE_FRAME_H // 2) - (ATTACK_BAR_H // 2) + ATTACK_BAR_Y_OFFSET
    cursor_y = bar_y - ATTACK_CURSOR_EXTRA_PX
    cursor_h = ATTACK_BAR_H + (ATTACK_CURSOR_EXTRA_PX * 2)
    if cursor_h < 1:
        cursor_h = 1

    if full_refresh:
        lgfx.clear()
        _draw_battle_frame()

        enemy_sprite_path, _, _ = _battle_enemy_sprite_info()
        enemy_drawn = False
        enemy_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_ENEMY_DRAW_W) // 2)
        enemy_y = battle_frame_y + 12
        if hasattr(lgfx, "draw_png_file") and _path_exists(enemy_sprite_path):
            enemy_drawn = bool(
                lgfx.draw_png_file(
                    enemy_sprite_path,
                    enemy_x,
                    enemy_y,
                    ATTACK_ENEMY_DRAW_W,
                    ATTACK_ENEMY_DRAW_H,
                )
            )
        if not enemy_drawn:
            lgfx.draw_circle(
                battle_frame_x + (BATTLE_FRAME_W // 2),
                enemy_y + (ATTACK_ENEMY_DRAW_H // 2),
                ATTACK_ENEMY_DRAW_H // 2,
                BATTLE_COLOR_WHITE,
            )

        if hasattr(lgfx, "draw_text"):
            hp_text = "ENEMY HP %d/%d" % (enemy_hp, ENEMY_HP_MAX)
            _draw_text_in_box(battle_frame_x + 8, enemy_y + ATTACK_ENEMY_DRAW_H + 4, BATTLE_FRAME_W - 16, 12, hp_text, BATTLE_COLOR_WHITE)

        hp_bar_x = battle_frame_x + ((BATTLE_FRAME_W - ENEMY_HP_BAR_W) // 2)
        hp_bar_y = enemy_y + ATTACK_ENEMY_DRAW_H + 18
        _draw_rect_thick(hp_bar_x, hp_bar_y, ENEMY_HP_BAR_W, ENEMY_HP_BAR_H, BATTLE_COLOR_WHITE, 1)
        hp_inner_x = hp_bar_x + 1
        hp_inner_y = hp_bar_y + 1
        hp_inner_w = ENEMY_HP_BAR_W - 2
        hp_inner_h = ENEMY_HP_BAR_H - 2
        if hp_inner_w > 0 and hp_inner_h > 0:
            _fill_rect_solid(hp_inner_x, hp_inner_y, hp_inner_w, hp_inner_h, ENEMY_HP_BAR_EMPTY_COLOR)
            enemy_hp_now = _clamp(enemy_hp, 0, ENEMY_HP_MAX)
            hp_fill_w = 0
            if ENEMY_HP_MAX > 0:
                hp_fill_w = (hp_inner_w * enemy_hp_now) // ENEMY_HP_MAX
            if hp_fill_w > 0:
                _fill_rect_solid(hp_inner_x, hp_inner_y, hp_fill_w, hp_inner_h, ENEMY_HP_BAR_FILL_COLOR)

        _draw_battle_status_line()

        _draw_attack_bar_static_layers(bar_x, bar_y)
        attack_prev_cursor_draw_x = -9999

    cursor_x = _clamp(attack_cursor_x, bar_x, bar_x + ATTACK_BAR_W - 1)
    cursor_draw_x = cursor_x - (ATTACK_CURSOR_W // 2)
    max_cursor_x = bar_x + ATTACK_BAR_W - ATTACK_CURSOR_W
    cursor_draw_x = _clamp(cursor_draw_x, bar_x, max_cursor_x)
    bar_top = bar_y
    bar_bottom = bar_y + ATTACK_BAR_H
    cursor_bottom = cursor_y + cursor_h
    if not full_refresh and attack_prev_cursor_draw_x > -9000:
        prev_x0 = attack_prev_cursor_draw_x
        prev_x1 = attack_prev_cursor_draw_x + ATTACK_CURSOR_W - 1
        curr_x0 = cursor_draw_x
        curr_x1 = cursor_draw_x + ATTACK_CURSOR_W - 1

        restore_x0 = prev_x0 if prev_x0 < curr_x0 else curr_x0
        restore_x1 = prev_x1 if prev_x1 > curr_x1 else curr_x1
        bar_min_x = bar_x
        bar_max_x = bar_x + ATTACK_BAR_W - 1
        if restore_x0 < bar_min_x:
            restore_x0 = bar_min_x
        if restore_x1 > bar_max_x:
            restore_x1 = bar_max_x
        if restore_x1 >= restore_x0:
            _draw_attack_bar_static_layers(bar_x, bar_y, restore_x0, restore_x1)

        # Only clear the old cursor segments outside the bar body.
        if cursor_y < bar_top:
            top_h = bar_top - cursor_y
            if top_h > 0:
                _clear_rect_black(prev_x0, cursor_y, ATTACK_CURSOR_W, top_h)
        if cursor_bottom > bar_bottom:
            bottom_h = cursor_bottom - bar_bottom
            if bottom_h > 0:
                _clear_rect_black(prev_x0, bar_bottom, ATTACK_CURSOR_W, bottom_h)

    if ATTACK_CURSOR_W >= 3:
        _fill_rect_solid(cursor_draw_x, cursor_y, 1, cursor_h, ATTACK_BAR_CURSOR_COLOR)
        _fill_rect_solid(cursor_draw_x + 1, cursor_y, ATTACK_CURSOR_W - 2, cursor_h, ATTACK_BAR_CURSOR_CORE_COLOR)
        _fill_rect_solid(cursor_draw_x + ATTACK_CURSOR_W - 1, cursor_y, 1, cursor_h, ATTACK_BAR_CURSOR_COLOR)
    else:
        _fill_rect_solid(cursor_draw_x, cursor_y, ATTACK_CURSOR_W, cursor_h, ATTACK_BAR_CURSOR_COLOR)

    attack_prev_cursor_draw_x = cursor_draw_x


def update_battle_menu(loop_start, fight_pressed, act_pressed, item_pressed, mercy_pressed):
    global mode, act_dialog_until_ms
    global battle_dialog_mode, mercy_exit_pending, battle_dialog_started_ms, battle_dialog_png_info, battle_dialog_text
    global battle_menu_dirty
    global act_menu_active, act_choice_index, act_sequence_step, act_nav_prev_dir
    global act_prev_selected_index, act_selection_dirty, act_menu_slot_cache
    global item_menu_active, item_choice_index, item_nav_prev_dir, item_menu_slot_cache
    global item_prev_selected_index, item_selection_dirty, item_view_offset
    global attack_started_ms, attack_cursor_x, attack_cursor_dir, attack_locked, battle_attack_dirty

    if _map1_story_is_active():
        _map1_story_update_menu(loop_start)
        return

    dialog_active = time.ticks_diff(act_dialog_until_ms, loop_start) > 0
    if mercy_exit_pending and not dialog_active:
        _exit_battle_to_explore()
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
            mode = MODE_BATTLE_ATTACK
            bar_min_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_BAR_W) // 2)
            attack_started_ms = loop_start
            attack_cursor_x = bar_min_x
            attack_cursor_dir = 1
            attack_locked = False
            battle_attack_dirty = True
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
                _battle_enemy_dialog_apply_entry(_battle_enemy_mercy_success_entry())
                act_dialog_until_ms = time.ticks_add(loop_start, MERCY_DIALOG_MS)
                battle_dialog_started_ms = loop_start
                mercy_exit_pending = True
            else:
                print("MERCY: locked")
                battle_dialog_mode = BATTLE_DIALOG_MERCY_LOCKED
                _battle_enemy_dialog_apply_entry(_battle_enemy_mercy_locked_entry())
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
            mode = MODE_BATTLE_ATTACK
            bar_min_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_BAR_W) // 2)
            attack_started_ms = loop_start
            attack_cursor_x = bar_min_x
            attack_cursor_dir = 1
            attack_locked = False
            battle_attack_dirty = True
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
                _battle_enemy_dialog_apply_entry(_battle_enemy_mercy_success_entry())
                act_dialog_until_ms = time.ticks_add(loop_start, MERCY_DIALOG_MS)
                battle_dialog_started_ms = loop_start
                mercy_exit_pending = True
            else:
                print("MERCY: locked")
                battle_dialog_mode = BATTLE_DIALOG_MERCY_LOCKED
                _battle_enemy_dialog_apply_entry(_battle_enemy_mercy_locked_entry())
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
            reply_index = 0
            if selected == 0:
                act_sequence_step = 1
                reply_index = 0
            elif selected == 1:
                if act_sequence_step == 1:
                    act_sequence_step = 2
                    reply_index = 1
                else:
                    act_sequence_step = 0
                    reply_index = 0
            else:
                if act_sequence_step == 2:
                    act_sequence_step = 3
                    reply_index = 2
                else:
                    act_sequence_step = 0
                    reply_index = 0
            _battle_enemy_dialog_apply_entry(_battle_enemy_act_reply_entry(reply_index))
            act_menu_active = False
            act_nav_prev_dir = 0
            act_menu_slot_cache = None
            act_prev_selected_index = -1
            act_selection_dirty = False
            battle_dialog_mode = BATTLE_DIALOG_ACT_REPLY
            battle_dialog_started_ms = loop_start
            act_dialog_until_ms = time.ticks_add(loop_start, ACT_REPLY_MS)
            battle_menu_dirty = True
        return

    if fight_pressed:
        mode = MODE_BATTLE_ATTACK
        bar_min_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_BAR_W) // 2)
        attack_started_ms = loop_start
        attack_cursor_x = bar_min_x
        attack_cursor_dir = 1
        attack_locked = False
        battle_attack_dirty = True
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
            _battle_enemy_dialog_apply_entry(_battle_enemy_mercy_success_entry())
            act_dialog_until_ms = time.ticks_add(loop_start, MERCY_DIALOG_MS)
            battle_dialog_started_ms = loop_start
            mercy_exit_pending = True
        else:
            print("MERCY: locked")
            battle_dialog_mode = BATTLE_DIALOG_MERCY_LOCKED
            _battle_enemy_dialog_apply_entry(_battle_enemy_mercy_locked_entry())
            act_dialog_until_ms = time.ticks_add(loop_start, ACT_REPLY_MS)
            battle_dialog_started_ms = loop_start
            mercy_exit_pending = False
        battle_menu_dirty = True


def update_battle_attack(loop_start, fight_pressed):
    global mode, enemy_hp, map6_boss_battle_active
    global attack_started_ms, attack_cursor_x, attack_cursor_dir, attack_locked, battle_attack_dirty
    global fight_return_deadline_ms, battle_fight_dirty, battle_status_dirty
    global battle_dialog_mode, battle_dialog_png_info, battle_dialog_text, act_dialog_until_ms
    global mercy_exit_pending

    bar_min_x = battle_frame_x + ((BATTLE_FRAME_W - ATTACK_BAR_W) // 2)
    bar_max_x = bar_min_x + ATTACK_BAR_W - 1
    if attack_started_ms == 0:
        attack_started_ms = loop_start
        attack_cursor_x = bar_min_x
        attack_cursor_dir = 1
        attack_locked = False
    if attack_cursor_x < bar_min_x:
        attack_cursor_x = bar_min_x
    elif attack_cursor_x > bar_max_x:
        attack_cursor_x = bar_max_x

    attack_cursor_x += attack_cursor_dir * ATTACK_CURSOR_SPEED_PX
    if attack_cursor_x <= bar_min_x:
        attack_cursor_x = bar_min_x
        attack_cursor_dir = 1
    elif attack_cursor_x >= bar_max_x:
        attack_cursor_x = bar_max_x
        attack_cursor_dir = -1

    timed_out = time.ticks_diff(loop_start, attack_started_ms) >= ATTACK_BAR_TIMEOUT_MS
    if (not fight_pressed) and (not timed_out):
        return

    attack_locked = True
    player_at = PLAYER_AT_BASE + PLAYER_AT_BONUS
    mult = 1
    if not timed_out:
        bar_center_x = bar_min_x + (ATTACK_BAR_W // 2)
        dist = abs(attack_cursor_x - bar_center_x)
        half = ATTACK_BAR_W // 2
        if dist <= (half * ATTACK_ZONE_PERFECT_PCT) // 100:
            mult = 3
        elif dist <= (half * ATTACK_ZONE_GOOD_PCT) // 100:
            mult = 2
    damage = player_at * mult
    if damage < 1:
        damage = 1
    enemy_hp -= damage
    if enemy_hp < 0:
        enemy_hp = 0
    battle_status_dirty = True
    print("attack_hit: mult", mult, "damage", damage, "enemy_hp", enemy_hp)

    if enemy_hp <= 0:
        if map6_boss_battle_active:
            _map6_boss_mark_defeated()
        _exit_battle_to_explore()
        return

    mode = MODE_BATTLE_FIGHT
    _reset_battle_state()
    fight_return_deadline_ms = time.ticks_add(loop_start, FIGHT_AUTO_RETURN_MS)
    battle_fight_dirty = True
    battle_dialog_mode = BATTLE_DIALOG_NONE
    battle_dialog_png_info = None
    battle_dialog_text = None
    act_dialog_until_ms = 0
    mercy_exit_pending = False


def update_battle_fight(loop_start):
    global mode, fight_heart_x, fight_heart_y
    global battle_menu_dirty, battle_dialog_visible, fight_return_deadline_ms
    global battle_fight_dirty, battle_bullets_dirty, battle_status_dirty
    global battle_dialog_mode, mercy_exit_pending, battle_dialog_png_info, battle_dialog_text, act_dialog_until_ms
    global battle_menu_full_clear_pending, battle_menu_static_ready, battle_menu_prev_dialog_active
    global act_menu_active, act_nav_prev_dir
    global item_menu_active, item_nav_prev_dir
    global bullets, next_bullet_spawn_ms, damage_invuln_until_ms, battle_prev_bullet_positions

    if _map1_story_is_active():
        _map1_story_update_fight(loop_start)
        return

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
        _reset_attack_state()
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
    global title_dirty, title_full_redraw
    global battle_prev_heart_x, battle_prev_heart_y
    global battle_menu_dirty, battle_fight_dirty, battle_dialog_visible, battle_heart_needs_sprite_refresh
    global battle_bullets_dirty, battle_prev_bullet_positions
    global battle_status_dirty, battle_attack_dirty
    global act_selection_dirty, act_prev_selected_index
    global item_selection_dirty
    global inv_screen_dirty
    global weapon_pickup_dialog_active, weapon_pickup_dialog_dirty

    if mode == MODE_TITLE_MENU:
        if title_dirty:
            _draw_title_menu_screen(loop_start, title_full_redraw)
            title_dirty = False
            title_full_redraw = False
        return

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
        _draw_ground_weapon_drops()
        _draw_map6_boss(loop_start, scene_redrawn, player_redrawn)
        if weapon_pickup_dialog_active:
            if weapon_pickup_dialog_dirty or scene_redrawn or player_redrawn:
                _draw_weapon_pickup_dialog()
                weapon_pickup_dialog_dirty = False
        if portal_transition_active:
            _draw_portal_transition_overlay(loop_start)
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
        if dialog_active and (not _map1_story_is_active()):
            _clear_battle_status_line_menu()
        else:
            _draw_battle_status_line(True)
        return

    if mode == MODE_BATTLE_ATTACK:
        if battle_attack_dirty:
            draw_battle_attack_screen(True)
            battle_attack_dirty = False
        else:
            draw_battle_attack_screen(False)
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

    # Keep one rendering path in fight mode to avoid rapid visual toggling.
    use_png_heart = can_draw_png and BATTLE_HEART_USE_PNG_ON_MOVE

    heart_drawn = False
    if use_png_heart:
        heart_drawn = _draw_battle_heart_sprite(fight_heart_x, fight_heart_y)
    if not heart_drawn:
        _draw_battle_heart_mask(fight_heart_x, fight_heart_y, BATTLE_COLOR_RED)
        battle_heart_needs_sprite_refresh = False

    # Repaint border after local erase paths so edge pixels remain stable.
    _draw_battle_frame()
    if battle_status_dirty or battle_fight_dirty:
        _draw_battle_status_line()
        battle_status_dirty = False

    battle_prev_heart_x = fight_heart_x
    battle_prev_heart_y = fight_heart_y
    battle_prev_bullet_positions = _get_bullet_positions()
    battle_bullets_dirty = False
    battle_fight_dirty = False

def _run_main_loop():
    global loop_start, frame_dt, prev_loop_ms, frame, encounter_cooldown_frames, teleport_cooldown_frames, rx, ry
    global neutral, dx_center, dx_mid, cx, dy_center, dy_mid, cy, x_dir
    global y_dir_raw, intro_neutral, spawn_intro_active, spawn_intro_cleared_once, explore_force_full_redraw, interact_sw_prev, interact_pressed, btn_fight_prev
    global fight_pressed, btn_act_prev, act_pressed, btn_item_prev, item_pressed, btn_mercy_prev, mercy_pressed, explore_moved
    global explore_scrolled, explore_anim_changed, move_dx, move_dy, active_portal, target_spawn, moved_since_last_map1, map1_opening_battle_timer_started
    global map1_opening_battle_due_ms, map1_opening_battle_done, move_dx_for_encounter, move_dy_for_encounter, move_dist_for_encounter, moved_since_last, encounter_enemy_id, lamp_dialog_until_ms
    global explore_overlay_dirty, dt, fps, avg_preload_ms, total_preload_attempts, avg_gc_ms, frame_used, map6_boss_battle_active
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
        if mode == MODE_EXPLORE and spawn_intro_active:
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
        if _map1_story_is_active():
            fight_pressed = False
            act_pressed = False
            item_pressed = False
            mercy_pressed = False

        if mode == MODE_TITLE_MENU:
            explore_moved = False
            explore_scrolled = False
            explore_anim_changed = False
            update_title_menu(loop_start, interact_pressed)
        elif mode == MODE_EXPLORE:
            if portal_transition_active:
                explore_moved = False
                explore_scrolled = False
                explore_anim_changed = False
                _portal_transition_update(loop_start)
            elif weapon_pickup_dialog_active:
                explore_moved = False
                explore_scrolled = False
                explore_anim_changed = False
                update_weapon_pickup_dialog(interact_pressed)
            else:
                update_player(loop_start, frame_dt)

                if mode == MODE_EXPLORE and item_pressed:
                    _open_explore_inventory()

                if mode == MODE_EXPLORE:
                    _update_preload_for_player(player_x, player_y)
                    _portal_transition_rearm_update(player_x, player_y)

                    if teleport_cooldown_frames == 0:
                        move_dx = player_x - prev_player_x
                        move_dy = player_y - prev_player_y
                        active_portal = _get_current_portal(player_x, player_y, move_dx, move_dy)
                        if active_portal:
                            if active_portal.get("transition_effect") == PORTAL_TRANSITION_EFFECT_SPOTLIGHT:
                                if not _portal_transition_rearm_blocked(active_portal):
                                    _portal_transition_start(active_portal)
                            else:
                                target_spawn = active_portal.get("target_spawn")
                                if target_spawn and len(target_spawn) >= 2:
                                    switch_map(active_portal["target_map_id"], target_spawn[0], target_spawn[1])
                                else:
                                    switch_map(active_portal["target_map_id"])

                    if mode == MODE_EXPLORE and current_map_id == MAP1_ID and (not map1_opening_battle_done):
                        moved_since_last_map1 = (player_x != prev_player_x) or (player_y != prev_player_y)
                        if moved_since_last_map1 and (not map1_opening_battle_timer_started):
                            map1_opening_battle_timer_started = True
                            map1_opening_battle_due_ms = time.ticks_add(loop_start, MAP1_OPENING_BATTLE_DELAY_MS)
                        if (
                            map1_opening_battle_timer_started
                            and encounter_cooldown_frames == 0
                            and teleport_cooldown_frames == 0
                            and time.ticks_diff(loop_start, map1_opening_battle_due_ms) >= 0
                        ):
                            map6_boss_battle_active = False
                            _start_battle_from_explore()
                            map1_opening_battle_done = True
                            map1_opening_battle_timer_started = False

                    if mode == MODE_EXPLORE:
                        move_dx_for_encounter = player_x - prev_player_x
                        move_dy_for_encounter = player_y - prev_player_y
                        move_dist_for_encounter = abs(move_dx_for_encounter) + abs(move_dy_for_encounter)
                        _encounter_note_travel(current_map_id, move_dist_for_encounter)

                    if mode == MODE_EXPLORE and encounter_cooldown_frames == 0 and teleport_cooldown_frames == 0:
                        if _map6_boss_trigger_hit(player_x, player_y):
                            map6_boss_battle_active = True
                            _start_battle_from_explore(enemy_id="MAP6_BOSS")
                        moved_since_last = (player_x != prev_player_x) or (player_y != prev_player_y)
                        if mode == MODE_EXPLORE and moved_since_last:
                            encounter_enemy_id = _encounter_try_start(current_map_id, player_x, player_y)
                            if encounter_enemy_id:
                                map6_boss_battle_active = False
                                _start_battle_from_explore(enemy_id=encounter_enemy_id)

                    if mode == MODE_EXPLORE and interact_pressed:
                        if _try_open_weapon_pickup_dialog():
                            pass
                        elif current_map_id == MAP1_ID and _in_rect(player_x, player_y, LAMP_INTERACT_RECT_PX):
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
        elif mode == MODE_BATTLE_ATTACK:
            explore_moved = False
            explore_scrolled = False
            explore_anim_changed = False
            update_battle_attack(loop_start, fight_pressed)
        else:
            explore_moved = False
            explore_scrolled = False
            explore_anim_changed = False
            update_battle_fight(loop_start)

        draw_all(loop_start)
        _resident_pump_preload()
        _maybe_run_deferred_gc(loop_start, explore_moved, explore_scrolled)

        if frame % 120 == 0:
            dt = time.ticks_diff(time.ticks_ms(), t0)
            fps = (frame * 1000 / dt) if dt else 0
            print("frame", frame, "fps", fps, "mode", mode, "cooldown", encounter_cooldown_frames, "stats", lgfx.stats(), "mem_free", gc.mem_free())
            if DEBUG_PERF:
                avg_preload_ms = 0
                total_preload_attempts = perf_preload_build_count + perf_preload_build_fail_count
                if total_preload_attempts > 0:
                    avg_preload_ms = perf_preload_build_ms_total // total_preload_attempts
                avg_gc_ms = 0
                if perf_gc_run_count > 0:
                    avg_gc_ms = perf_gc_run_ms_total // perf_gc_run_count
                print(
                    "perf_preload",
                    "build_ok", perf_preload_build_count,
                    "build_fail", perf_preload_build_fail_count,
                    "release", perf_preload_release_count,
                    "skip_cached", perf_preload_skip_cached,
                    "skip_cooldown", perf_preload_skip_cooldown,
                    "skip_debounce", perf_preload_skip_debounce,
                    "skip_dwell", perf_preload_skip_dwell,
                    "skip_same_zone", perf_preload_skip_same_zone,
                    "skip_motion", perf_preload_skip_motion,
                    "skip_post_switch", perf_preload_skip_post_switch,
                    "avg_ms", avg_preload_ms,
                )
                print(
                    "perf_gc",
                    "run", perf_gc_run_count,
                    "avg_ms", avg_gc_ms,
                    "pending", gc_pending,
                )

        if mode == MODE_EXPLORE and not explore_moved and not explore_scrolled:
            time.sleep_ms(1)
        if TARGET_FRAME_MS > 0:
            frame_used = time.ticks_diff(time.ticks_ms(), loop_start)
            if frame_used < TARGET_FRAME_MS:
                time.sleep_ms(TARGET_FRAME_MS - frame_used)


def main():
    _init_display()
    _play_boot_comic_intro()
    _init_runtime_state()
    _run_main_loop()
