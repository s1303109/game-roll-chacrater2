#!/bin/bash
# Changed-only deploy script for ESP32-S3 + MicroPython.
# It compares local/remote size+hash and copies only changed files,
# waits 0.5s between mpremote commands, then runs import main.

set -u
set -o pipefail

PORT="${MP_PORT:-/dev/ttyACM0}"
ASSET_DIR="${ASSET_DIR:-/workspace/row/assets/out}"
APP_DIR="${APP_DIR:-/workspace/row/app}"
SD_ASSET_DIR="${SD_ASSET_DIR:-/sd/out}"
MAIN_SRC="${MAIN_SRC:-${APP_DIR}/main.py}"
GAME_SRC="${GAME_SRC:-${APP_DIR}/game_mvp.py}"
BOOT_SRC="${BOOT_SRC:-${APP_DIR}/boot.py}"
SD_HOST_SRC="${SD_HOST_SRC:-${APP_DIR}/sd_host.py}"
SPAWN_OVERLAY_NAME="${SPAWN_OVERLAY_NAME:-spawn_closed_eyes_32x32.rgb565}"
SPAWN_OVERLAY_SRC="${SPAWN_OVERLAY_SRC:-${ASSET_DIR}/spawn_closed_eyes_32x32.rgb565}"
INVENTORY_PORTRAIT_NAME="${INVENTORY_PORTRAIT_NAME:-inventory_portrait.png}"
INVENTORY_PORTRAIT_SRC="${INVENTORY_PORTRAIT_SRC:-/workspace/inventory_portrait.png}"
COVER_NAME="${COVER_NAME:-front_cover_320x240.png}"
COVER_SRC="${COVER_SRC:-/workspace/front_cover_320x240.png}"
TITLE_UI_START_NAME="${TITLE_UI_START_NAME:-title_ui_start_112x54.png}"
TITLE_UI_START_SRC="${TITLE_UI_START_SRC:-/workspace/title_ui_start_112x54.png}"
TITLE_UI_CONTINUE_NAME="${TITLE_UI_CONTINUE_NAME:-title_ui_continue_112x54.png}"
TITLE_UI_CONTINUE_SRC="${TITLE_UI_CONTINUE_SRC:-/workspace/title_ui_continue_112x54.png}"
BOOT_COMIC_DIR="${BOOT_COMIC_DIR:-/workspace}"

# Prefer system mpremote. Fallback to repo-local mpremote module.
if command -v mpremote >/dev/null 2>&1; then
  MPREMOTE=(mpremote)
else
  MPREMOTE=(python -m mpremote)
  export PYTHONPATH="${PYTHONPATH:-/workspace/micropython/tools/mpremote}"
fi

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

run_mpremote() {
  "${MPREMOTE[@]}" "$@"
}

local_sha256() {
  local path="$1"
  sha256sum "${path}" | awk '{print $1}'
}

remote_meta_hash() {
  local name="$1"
  local out
  local py

  py=$(cat <<PY
import os
try:
  import hashlib
except ImportError:
  hashlib = None
try:
  import ubinascii as binascii
except ImportError:
  import binascii

name = "${name}"
try:
  size = os.stat(name)[6]
except OSError:
  print("-1 missing")
else:
  if hashlib is None or not hasattr(hashlib, "sha256"):
    print("%d nohash" % size)
  else:
    h = hashlib.sha256()
    with open(name, "rb") as f:
      while True:
        b = f.read(4096)
        if not b:
          break
        h.update(b)
    print("%d %s" % (size, binascii.hexlify(h.digest()).decode()))
PY
)

  if ! out="$(run_mpremote connect "${PORT}" exec "${py}")"; then
    return 1
  fi

  # Keep a small gap to avoid USB busy issues.
  sleep 0.5

  # mpremote may include extra lines; use the last line.
  printf '%s\n' "${out}" | tail -n 1 | tr -d '\r'
}

copy_if_changed() {
  local src="$1"
  local remote="$2"
  local label="${3:-${remote}}"
  local lsize
  local lhash
  local rsize
  local rhash
  local rmeta

  if [[ ! -f "${src}" ]]; then
    fail "Local file not found: ${src}"
  fi

  lsize="$(stat -c%s "${src}")"
  lhash="$(local_sha256 "${src}")"

  if ! rmeta="$(remote_meta_hash "${remote}")"; then
    fail "Failed to read remote metadata for ${remote}"
  fi

  rsize="$(printf '%s' "${rmeta}" | awk '{print $1}')"
  rhash="$(printf '%s' "${rmeta}" | awk '{print $2}')"

  if [[ ! "${rsize}" =~ ^-?[0-9]+$ ]]; then
    fail "Unexpected remote metadata output for ${remote}: ${rmeta}"
  fi

  if [[ "${rsize}" -eq "${lsize}" && "${rhash}" == "${lhash}" ]]; then
    echo "Skipping ${label} -> ${remote} (same size+hash: ${lsize} bytes)"
    return 0
  fi

  echo "Copying ${label} -> ${remote}..."
  if ! run_mpremote connect "${PORT}" fs cp "${src}" ":${remote}"; then
    fail "Failed to copy ${label} to ${remote} on ${PORT}"
  fi

  # Keep a small gap to avoid USB busy issues.
  sleep 0.5
}

prepare_sd() {
  local py
  py=$(cat <<'PY'
import os
try:
  from sd_host import mount_sd
except Exception:
  mount_sd = None

if mount_sd:
  try:
    mount_sd("/sd", return_ok=True)
  except Exception:
    pass

for path in ("/sd", "/sd/app", "/sd/out"):
  cur = ""
  for part in path.split("/"):
    if not part:
      continue
    cur += "/" + part
    try:
      os.stat(cur)
    except OSError:
      try:
        os.mkdir(cur)
      except OSError:
        pass
print("sd_ready")
PY
)
  run_mpremote connect "${PORT}" exec "${py}" >/dev/null
  sleep 0.5
}

prepare_sd

for name in map.json tilemap.bin tileset.bin collision.bin player_sheet.rgb565; do
  copy_if_changed "${ASSET_DIR}/${name}" "/${name}" "${name}"
done

copy_if_changed "${BOOT_SRC}" "/boot.py" "boot.py"
copy_if_changed "${SD_HOST_SRC}" "/sd_host.py" "sd_host.py"
copy_if_changed "${MAIN_SRC}" "/main.py" "main.py"
copy_if_changed "${GAME_SRC}" "/game_mvp.py" "game_mvp.py"
copy_if_changed "${SPAWN_OVERLAY_SRC}" "/${SPAWN_OVERLAY_NAME}" "${SPAWN_OVERLAY_NAME}"
copy_if_changed "${INVENTORY_PORTRAIT_SRC}" "/${INVENTORY_PORTRAIT_NAME}" "${INVENTORY_PORTRAIT_NAME}"
copy_if_changed "${COVER_SRC}" "/${COVER_NAME}" "${COVER_NAME}"
copy_if_changed "${TITLE_UI_START_SRC}" "/${TITLE_UI_START_NAME}" "${TITLE_UI_START_NAME}"
copy_if_changed "${TITLE_UI_CONTINUE_SRC}" "/${TITLE_UI_CONTINUE_NAME}" "${TITLE_UI_CONTINUE_NAME}"

for i in 01 02 03 04 05 06; do
  copy_if_changed "${BOOT_COMIC_DIR}/comic_${i}_320x240.png" "/comic_${i}_320x240.png" "comic_${i}_320x240.png"
done

sync_assets_to_sd() {
  local py
  py=$(cat <<'PY'
import os
import time
try:
  from sd_host import mount_sd
except Exception:
  mount_sd = None

if mount_sd:
  try:
    mount_sd("/sd", return_ok=True)
  except Exception:
    pass

def ensure_dir(path):
  cur = ""
  for part in path.split("/"):
    if not part:
      continue
    cur += "/" + part
    try:
      os.stat(cur)
    except OSError:
      try:
        os.mkdir(cur)
      except OSError:
        pass

def copy_file(src, dst):
  tmp = dst + ".tmp"
  try:
    os.remove(tmp)
  except OSError:
    pass
  with open(src, "rb") as fin, open(tmp, "wb") as fout:
    while True:
      b = fin.read(4096)
      if not b:
        break
      fout.write(b)
  try:
    os.remove(dst)
  except OSError:
    pass
  os.rename(tmp, dst)

ensure_dir("/sd/out")
for name in ("map.json", "tilemap.bin", "tileset.bin", "collision.bin", "player_sheet.rgb565", "spawn_closed_eyes_32x32.rgb565"):
  copy_file("/" + name, "/sd/out/" + name)
print("sd_sync_ok")
PY
)
  run_mpremote connect "${PORT}" exec "${py}" >/dev/null
  sleep 0.5
}

sync_assets_to_sd

echo "Running import main..."
if ! run_mpremote connect "${PORT}" exec "import main"; then
  fail "Failed to run 'import main' on ${PORT}"
fi

echo "Deploy (changed only) succeeded."
