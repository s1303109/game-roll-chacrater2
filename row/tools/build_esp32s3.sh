#!/usr/bin/env bash
set -euo pipefail

IDF_PATH="${IDF_PATH:-/opt/esp/idf}"
if [ ! -f "$IDF_PATH/export.sh" ]; then
  echo "error: IDF export script not found: $IDF_PATH/export.sh"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_C_MODULES="$ROOT_DIR/modules/micropython.cmake"
BOARD_VARIANT="${BOARD_VARIANT:-SPIRAM_OCT}"

if [ -d "$ROOT_DIR/micropython/ports/esp32" ]; then
  MP_ESP32_DIR="$ROOT_DIR/micropython/ports/esp32"
elif [ -d "/workspace/micropython/ports/esp32" ]; then
  MP_ESP32_DIR="/workspace/micropython/ports/esp32"
else
  echo "error: MicroPython esp32 port not found"
  echo " tried: $ROOT_DIR/micropython/ports/esp32"
  echo " tried: /workspace/micropython/ports/esp32"
  exit 1
fi

. "$IDF_PATH/export.sh" >/dev/null

cd "$MP_ESP32_DIR"
make BOARD=ESP32_GENERIC_S3 BOARD_VARIANT="$BOARD_VARIANT" USER_C_MODULES="$USER_C_MODULES" "$@"
