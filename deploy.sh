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

copy_one() {
  local src="$1"
  local remote="$2"
  local label="${3:-$2}"
  [[ -f "$src" ]] || fail "Local file not found: $src"
  echo "Copying ${label} -> ${remote}"
  if [[ "$remote" == /sd/* ]]; then
    run_mpremote_with_sd fs cp "$src" ":$remote"
  else
    run_mpremote connect "$PORT" fs cp "$src" ":$remote"
  fi
  sleep 0.5
}

verify_required_sources() {
  local spec src dst dir name

  for spec in "${FLASH_FILES[@]}" "${GAME_FILES[@]}"; do
    src="${spec%%:*}"
    [[ -f "$src" ]] || fail "Missing required source: $src"
  done

  [[ -f "${ASSET_ROOT}/out/player_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/player_sheet.rgb565"

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
from sd_host import mount_sd

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

for path in (
    "/sd/game",
    "/sd/game/assets",
    "/sd/game/assets/out",
    "/sd/game/assets/out_map2",
    "/sd/game/assets/out_map3",
    "/sd/game/assets/out_map4",
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
prepare_device
copy_game_files
run_game

echo "Deploy succeeded."
