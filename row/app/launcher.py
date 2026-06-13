import gc
import os
import sys
import time

from sd_host import ensure_sd_32gb, mount_sd, sd_capacity_bytes


GAME_ROOT = "/sd/game"
STALE_FLASH_FILES = (
    "/lgfx.py",
    "/game_mvp.py",
    "/config.py",
    "/map_registry.py",
    "/map.json",
    "/tilemap.bin",
    "/tileset.bin",
    "/collision.bin",
    "/player_sheet.rgb565",
    "/front_cover_320x240.png",
    "/title_ui_start_112x54.png",
    "/title_ui_continue_112x54.png",
    "/comic_01_320x240.png",
    "/comic_02_320x240.png",
    "/comic_03_320x240.png",
    "/comic_04_320x240.png",
    "/comic_05_320x240.png",
    "/comic_06_320x240.png",
    "/inventory_portrait.png",
    "/heart_clean_18.png",
    "/heart.png",
    "/star_icon_24.png",
    "/enemy.png",
    "/FLOWEY.png",
    "/ANGRY FLOWEY.png",
    "/FLOWEY_anim_96.png",
    "/ANGRY FLOWEY_anim_96.png",
    "/fire ball.png",
    "/fire ball small.png",
    "/fire ball_anim_64.png",
    "/kind people.png",
    "/kind people_anim_96.png",
    "/map1_story_line_01.png",
    "/map1_story_line_02.png",
    "/map1_story_line_03.png",
    "/map1_story_line_04.png",
    "/map1_story_line_05.png",
    "/map1_story_line_06.png",
    "/map1_story_line_07.png",
    "/map1_story_line_08.png",
    "/map1_story_line_09.png",
    "/map1_story_line_10.png",
    "/map1_story_line_11.png",
    "/map1_story_line_12.png",
    "/map1_story_line_13.png",
    "/map1_story_line_14.png",
    "/map1_story_line_15.png",
    "/map1_story_line_16.png",
    "/map1_story_line_17.png",
    "/map1_story_line_18.png",
    "/fight_icon.png",
    "/act_icon.png",
    "/item_icon.png",
    "/mercy_icon.png",
    "/act_dialog_text.png",
    "/mercy_dialog_text.png",
    "/lamp_dialog_text.png",
    "/wood_up_bed_dialog.png",
    "/wood_up_mirror_dialog.png",
    "/wood_up_bookshelf_dialog.png",
    "/act_opt1_text.png",
    "/act_opt2_text.png",
    "/act_opt3_text.png",
    "/act_reply1_text.png",
    "/act_reply2_text.png",
    "/act_reply3_text.png",
    "/mercy_locked_text.png",
    "/main character close eyes.clean.png",
    "/main character close eyes.orig.png",
    "/titleui.png",
    "/comic_.png",
    "/spawn_closed_eyes_32x32.rgb565",
)


def _path_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _ensure_game_path():
    if GAME_ROOT in sys.path:
        sys.path.remove(GAME_ROOT)
    sys.path.insert(0, GAME_ROOT)


def _clear_game_modules():
    for name in list(sys.modules):
        if name in ("config", "map_registry", "game_mvp") or name.startswith("game_mvp."):
            del sys.modules[name]


def _report_stale_flash_files():
    stale = []
    for path in STALE_FLASH_FILES:
        if _path_exists(path):
            stale.append(path)
    for path in stale:
        print("[launcher] stale flash file ignored:", path)


def _mount_sd_with_retry():
    # Some boards/cards need one extra attempt right after reset.
    freqs = (8_000_000, 4_000_000, 12_000_000, 20_000_000)
    for attempt in range(2):
        for freq in freqs:
            try:
                if mount_sd("/sd", freq=freq, return_ok=True):
                    print("[launcher] sd_mounted: True freq:", freq, "attempt:", attempt + 1)
                    return
            except Exception as err:
                print("[launcher] sd_mount_retry_fail:", freq, "attempt:", attempt + 1, "err:", err)
            time.sleep_ms(30)
    raise RuntimeError("SD_MOUNT_FAILED")


def guard_psram_required():
    build = getattr(sys.implementation, "_build", "")
    if "SPIRAM_OCT" not in build:
        print("[ERROR] PSRAM_BUILD_MISMATCH: firmware is not SPIRAM_OCT.")
        print("[ERROR] build =", build)
        raise SystemExit("PSRAM_BUILD_MISMATCH")

    mem_free = gc.mem_free()
    if mem_free < 3_000_000:
        print("[ERROR] PSRAM_MEM_TOO_LOW: gc.mem_free() is below 3000000, this is likely not the expected PSRAM heap configuration.")
        print("[ERROR] mem_free =", mem_free)
        raise SystemExit("PSRAM_MEM_TOO_LOW")

    print("[OK] PSRAM guard passed.")
    print("[OK] build =", build)
    print("[OK] mem_free =", mem_free)


def _bootstrap_game_main():
    guard_psram_required()
    try:
        _mount_sd_with_retry()
        sd_capacity, sd_source = ensure_sd_32gb("/sd")
        print("[launcher] sd_capacity_ok:", sd_capacity, "source:", sd_source)
    except Exception as err:
        cap, source = sd_capacity_bytes("/sd")
        if cap is not None:
            print("[launcher] sd_capacity_detected:", cap, "source:", source)
        print("[launcher] SD mount/capacity failed:", err)
        raise

    if not _path_exists(GAME_ROOT):
        print("[launcher] missing file:", GAME_ROOT)
        raise RuntimeError("GAME_ROOT_MISSING")

    _ensure_game_path()
    _clear_game_modules()
    _report_stale_flash_files()

    try:
        import config
        import map_registry

        config.validate_cartridge(map_registry.MAP_REGISTRY)
        import game_mvp
    except Exception as err:
        print("[launcher] cartridge load failed:", err)
        raise

    game_main = getattr(game_mvp, "main", None)
    if game_main is None:
        print("[launcher] game_mvp.py has no main()")
        raise RuntimeError("GAME_MAIN_MISSING")

    return game_main


def _release_boot_memory():
    global STALE_FLASH_FILES, ensure_sd_32gb, mount_sd, sd_capacity_bytes
    global os, time
    global _path_exists, _ensure_game_path, _clear_game_modules
    global _report_stale_flash_files, _mount_sd_with_retry, guard_psram_required

    STALE_FLASH_FILES = ()
    ensure_sd_32gb = None
    mount_sd = None
    sd_capacity_bytes = None
    os = None
    time = None
    _path_exists = None
    _ensure_game_path = None
    _clear_game_modules = None
    _report_stale_flash_files = None
    _mount_sd_with_retry = None
    guard_psram_required = None
    sys.modules.pop(__name__, None)


def main():
    game_main = _bootstrap_game_main()
    _release_boot_memory()
    gc.collect()
    try:
        game_main()
    except Exception as err:
        print("[launcher] game start failed:", err)
        raise
