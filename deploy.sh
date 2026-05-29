#!/bin/bash
set -euo pipefail

PORT="${MP_PORT:-/dev/ttyACM0}"
APP_DIR="${APP_DIR:-/workspace/row/app}"
ASSET_ROOT="${ASSET_ROOT:-/workspace/row/assets}"
UI_SRC_DIR="${UI_SRC_DIR:-/workspace}"

if command -v mpremote >/dev/null 2>&1; then
  MPREMOTE=(mpremote)
else
  MPREMOTE=(python -m mpremote)
  export PYTHONPATH="${PYTHONPATH:-/workspace/micropython/tools/mpremote}"
fi

FLASH_FILES=(
  "${APP_DIR}/boot.py:/boot.py"
  "${APP_DIR}/main.py:/main.py"
  "${APP_DIR}/launcher.py:/launcher.py"
  "${APP_DIR}/sd_host.py:/sd_host.py"
)

GAME_FILES=(
  "${APP_DIR}/game_mvp.py:/sd/game/game_mvp.py"
  "${APP_DIR}/config.py:/sd/game/config.py"
  "${APP_DIR}/map_registry.py:/sd/game/map_registry.py"
)

MAP_DIRS=(
  "out"
  "out_map2"
  "out_map3"
  "out_map4"
  "out_map5"
  "out_map6"
  "out_map7"
  "out_map8"
  "out_map9"
  "out_map10"
  "out_map11"
  "out_wood_main"
  "out_wood_up"
  "out_wood_right"
  "out_wood_left"
)

UI_FILE_MAP=(
  "front_cover_320x240.png|front_cover_320x240.png"
  "title_ui_start_112x54.png|title_ui_start_112x54.png"
  "title_ui_continue_112x54.png|title_ui_continue_112x54.png"
  "comic_01_320x240.png|comic_01_320x240.png"
  "comic_02_320x240.png|comic_02_320x240.png"
  "comic_03_320x240.png|comic_03_320x240.png"
  "comic_04_320x240.png|comic_04_320x240.png"
  "comic_05_320x240.png|comic_05_320x240.png"
  "comic_06_320x240.png|comic_06_320x240.png"
  "inventory_portrait.png|inventory_portrait.png"
  "heart_clean_18.png|heart_clean_18.png"
  "heart.png|heart.png"
  "star_icon_24.png|star_icon_24.png"
  "enemy_clean.png|enemy.png"
  "FLOWEY.png|FLOWEY.png"
  "ANGRY FLOWEY.png|ANGRY FLOWEY.png"
  "map1_story_line_01.png|map1_story_line_01.png"
  "map1_story_line_02.png|map1_story_line_02.png"
  "map1_story_line_03.png|map1_story_line_03.png"
  "map1_story_line_04.png|map1_story_line_04.png"
  "map1_story_line_05.png|map1_story_line_05.png"
  "map1_story_line_06.png|map1_story_line_06.png"
  "map1_story_line_07.png|map1_story_line_07.png"
  "map1_story_line_08.png|map1_story_line_08.png"
  "map1_story_line_09.png|map1_story_line_09.png"
  "map1_story_line_10.png|map1_story_line_10.png"
  "fight_icon.png|fight_icon.png"
  "act_icon.png|act_icon.png"
  "item_icon.png|item_icon.png"
  "mercy_icon.png|mercy_icon.png"
  "act_dialog_text.png|act_dialog_text.png"
  "mercy_dialog_text.png|mercy_dialog_text.png"
  "lamp_dialog_text.png|lamp_dialog_text.png"
  "act_opt1_text.png|act_opt1_text.png"
  "act_opt2_text.png|act_opt2_text.png"
  "act_opt3_text.png|act_opt3_text.png"
  "act_reply1_text.png|act_reply1_text.png"
  "act_reply2_text.png|act_reply2_text.png"
  "act_reply3_text.png|act_reply3_text.png"
  "mercy_locked_text.png|mercy_locked_text.png"
  "map6_boss_battle.png|map6_boss_battle.png"
  "main character close eyes.clean.png|main character close eyes.clean.png"
  "main character close eyes.orig.png|main character close eyes.orig.png"
)

run_mpremote() {
  "${MPREMOTE[@]}" "$@"
}

run_mpremote_with_sd() {
  run_mpremote connect "$PORT" exec "from sd_host import mount_sd; mount_sd('/sd', return_ok=True)" "$@"
}

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

copy_with_fallback() {
  local src="$1"
  local remote="$2"
  local label="${3:-$2}"

  if [[ "$remote" == /sd/* ]]; then
    if run_mpremote_with_sd fs cp "$src" ":$remote"; then
      sleep 0.5
      return 0
    fi
  else
    if run_mpremote connect "$PORT" fs cp "$src" ":$remote"; then
      sleep 0.5
      return 0
    fi
  fi

  echo "fs cp failed for ${label}; fallback to SerialTransport.fs_writefile chunked..."
  python - "$PORT" "$src" "$remote" <<'PY'
import os
import sys

port, src, remote = sys.argv[1], sys.argv[2], sys.argv[3]
repo_mpremote = "/workspace/micropython/tools/mpremote"
if repo_mpremote not in sys.path:
    sys.path.insert(0, repo_mpremote)

from mpremote.transport_serial import SerialTransport

t = SerialTransport(port, baudrate=115200)
try:
    t.enter_raw_repl(soft_reset=False)
    if remote.startswith("/sd/"):
        t.exec("from sd_host import mount_sd\nmount_sd('/sd', return_ok=True)")
    with open(src, "rb") as f:
        data = f.read()
    t.fs_writefile(remote, data, chunk_size=1024)
finally:
    try:
        if t.in_raw_repl:
            t.exit_raw_repl()
    finally:
        t.close()

print("fallback_chunk_write_ok:", remote, "bytes:", os.path.getsize(src))
PY
  sleep 0.5
}

copy_one() {
  local src="$1"
  local remote="$2"
  local label="${3:-$2}"
  [[ -f "$src" ]] || fail "Local file not found: $src"
  echo "Copying ${label} -> ${remote}"
  copy_with_fallback "$src" "$remote" "$label"
}

verify_required_sources() {
  local spec src dst dir name

  for spec in "${FLASH_FILES[@]}" "${GAME_FILES[@]}"; do
    src="${spec%%:*}"
    [[ -f "$src" ]] || fail "Missing required source: $src"
  done

  [[ -f "${ASSET_ROOT}/out/player_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/player_sheet.rgb565"
  [[ -f "${ASSET_ROOT}/out/map6_boss_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/map6_boss_sheet.rgb565"

  for dir in "${MAP_DIRS[@]}"; do
    for name in map.json tilemap.bin tileset.bin collision.bin; do
      [[ -f "${ASSET_ROOT}/${dir}/${name}" ]] || fail "Missing map asset: ${ASSET_ROOT}/${dir}/${name}"
    done
  done

  for spec in "${UI_FILE_MAP[@]}"; do
    src="${spec%%|*}"
    [[ -f "${UI_SRC_DIR}/${src}" ]] || fail "Missing UI asset: ${UI_SRC_DIR}/${src}"
  done
}

check_psram_firmware() {
  local py
  py=$(cat <<'PY'
import gc
import sys

build = getattr(sys.implementation, "_build", "")
mem_free = gc.mem_free()
print("fw_build:", build)
print("fw_mem_free:", mem_free)
if "SPIRAM_OCT" not in build:
    print("[ERROR] PSRAM_BUILD_MISMATCH: firmware is not SPIRAM_OCT.")
    print("[ERROR] build =", build)
    raise RuntimeError("PSRAM_BUILD_MISMATCH")
if mem_free < 4_000_000:
    print("[ERROR] PSRAM_MEM_TOO_LOW: gc.mem_free() is below 4000000, this is likely not 8MB PSRAM firmware.")
    print("[ERROR] mem_free =", mem_free)
    raise RuntimeError("PSRAM_MEM_TOO_LOW")
PY
)
  run_mpremote connect "$PORT" exec "$py"
  sleep 0.5
}

check_sd_capacity_32gb() {
  local py
  py=$(cat <<'PY'
from sd_host import ensure_sd_32gb, mount_sd, sd_capacity_bytes

if not mount_sd("/sd", return_ok=True):
    raise RuntimeError("SD_MOUNT_FAILED")

cap, source = ensure_sd_32gb("/sd")
print("sd_capacity_ok:", cap, "source:", source)
probe_cap, probe_source = sd_capacity_bytes("/sd")
print("sd_capacity_probe:", probe_cap, "source:", probe_source)
PY
)
  run_mpremote connect "$PORT" exec "$py"
  sleep 0.5
}

copy_flash_files() {
  local spec src dst
  for spec in "${FLASH_FILES[@]}"; do
    src="${spec%%:*}"
    dst="${spec#*:}"
    copy_one "$src" "$dst" "$dst"
  done
}

prepare_device() {
  local py stale_py
  py=$(cat <<'PY'
import os
from sd_host import ensure_sd_32gb, mount_sd

STALE_FLASH_FILES = (
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
    "/fight_icon.png",
    "/act_icon.png",
    "/item_icon.png",
    "/mercy_icon.png",
    "/act_dialog_text.png",
    "/mercy_dialog_text.png",
    "/lamp_dialog_text.png",
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


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def ensure_dir(path):
    cur = ""
    for part in path.split("/"):
        if not part:
            continue
        cur += "/" + part
        try:
            os.stat(cur)
        except OSError:
            os.mkdir(cur)

if not mount_sd("/sd", return_ok=True):
    raise RuntimeError("SD_MOUNT_FAILED")
ensure_sd_32gb("/sd")

for path in (
    "/sd/game",
    "/sd/game/assets",
    "/sd/game/assets/out",
    "/sd/game/assets/out_map2",
    "/sd/game/assets/out_map3",
    "/sd/game/assets/out_map4",
    "/sd/game/assets/out_map5",
    "/sd/game/assets/out_map6",
    "/sd/game/assets/out_map7",
    "/sd/game/assets/out_map8",
    "/sd/game/assets/out_map9",
    "/sd/game/assets/out_map10",
    "/sd/game/assets/out_map11",
    "/sd/game/assets/out_wood_main",
    "/sd/game/assets/out_wood_up",
    "/sd/game/assets/out_wood_right",
    "/sd/game/assets/out_wood_left",
    "/sd/game/ui",
    "/sd/game/sprites",
    "/sd/game/save",
):
    ensure_dir(path)

for path in STALE_FLASH_FILES:
    try:
        os.remove(path)
        print("removed stale:", path)
    except OSError:
        if exists(path):
            print("stale ignored:", path)

print("device_ready")
PY
)
  run_mpremote connect "$PORT" exec "$py"
  sleep 0.5
}

copy_game_files() {
  local spec src dst dir name

  for spec in "${GAME_FILES[@]}"; do
    src="${spec%%:*}"
    dst="${spec#*:}"
    copy_one "$src" "$dst" "$dst"
  done

  copy_one "${ASSET_ROOT}/out/player_sheet.rgb565" "/sd/game/sprites/player_sheet.rgb565" "/sd/game/sprites/player_sheet.rgb565"
  copy_one "${ASSET_ROOT}/out/map6_boss_sheet.rgb565" "/sd/game/sprites/map6_boss_sheet.rgb565" "/sd/game/sprites/map6_boss_sheet.rgb565"

  for dir in "${MAP_DIRS[@]}"; do
    for name in map.json tilemap.bin tileset.bin collision.bin; do
      copy_one "${ASSET_ROOT}/${dir}/${name}" "/sd/game/assets/${dir}/${name}" "/sd/game/assets/${dir}/${name}"
    done
  done

  local spec src_name dst_name
  for spec in "${UI_FILE_MAP[@]}"; do
    src_name="${spec%%|*}"
    dst_name="${spec#*|}"
    copy_one "${UI_SRC_DIR}/${src_name}" "/sd/game/ui/${dst_name}" "/sd/game/ui/${dst_name}"
  done
}

run_game() {
  echo "Resetting board to boot launcher..."
  run_mpremote connect "$PORT" reset
}

verify_required_sources
copy_flash_files
check_psram_firmware
check_sd_capacity_32gb
prepare_device
copy_game_files
run_game

echo "Deploy succeeded."
