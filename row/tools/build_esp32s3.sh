#!/usr/bin/env bash
set -euo pipefail

IDF_PATH="${IDF_PATH:-/opt/esp/idf}"
if [ ! -f "$IDF_PATH/export.sh" ]; then
  echo "error: IDF export script not found: $IDF_PATH/export.sh"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_C_MODULES="$ROOT_DIR/modules/micropython.cmake"
ENV_BOARD_VARIANT="${BOARD_VARIANT-}"
ENV_BOARD="${BOARD-}"
BOARD="ROW_ESP32S3_16MB"
BOARD_VARIANT="SPIRAM_OCT"

if [[ -n "${ENV_BOARD_VARIANT}" && "${ENV_BOARD_VARIANT}" != "SPIRAM_OCT" ]]; then
  echo "[ERROR] BUILD_VARIANT_BLOCKED: only SPIRAM_OCT is allowed for this project."
  exit 1
fi
if [[ -n "${ENV_BOARD}" && "${ENV_BOARD}" != "ROW_ESP32S3_16MB" ]]; then
  echo "[ERROR] BUILD_VARIANT_BLOCKED: only ROW_ESP32S3_16MB is allowed for this project."
  exit 1
fi

FORWARD_ARGS=()
for arg in "$@"; do
  case "$arg" in
    BOARD_VARIANT=*)
      val="${arg#BOARD_VARIANT=}"
      if [[ "$val" != "SPIRAM_OCT" ]]; then
        echo "[ERROR] BUILD_VARIANT_BLOCKED: only SPIRAM_OCT is allowed for this project."
        exit 1
      fi
      ;;
    BOARD=*)
      val="${arg#BOARD=}"
      if [[ "$val" != "ROW_ESP32S3_16MB" ]]; then
        echo "[ERROR] BUILD_VARIANT_BLOCKED: only ROW_ESP32S3_16MB is allowed for this project."
        exit 1
      fi
      ;;
    *)
      FORWARD_ARGS+=("$arg")
      ;;
  esac
done

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
echo "Building BOARD=$BOARD BOARD_VARIANT=$BOARD_VARIANT USER_C_MODULES=$USER_C_MODULES"
make BOARD="$BOARD" BOARD_VARIANT="$BOARD_VARIANT" USER_C_MODULES="$USER_C_MODULES" "${FORWARD_ARGS[@]}"

BUILD_DIR="$MP_ESP32_DIR/build-${BOARD}-${BOARD_VARIANT}"
APP_PARTITION_SIZE=$((0x800000))
MIN_FREE_BYTES=$((128 * 1024))
MICROPY_BIN="$BUILD_DIR/micropython.bin"

if [[ -f "$BUILD_DIR/sdkconfig" ]]; then
  grep -E 'CONFIG_ESPTOOLPY_FLASHSIZE=|CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=' "$BUILD_DIR/sdkconfig" || true
fi

if [[ -f "$MICROPY_BIN" ]]; then
  micropython_size="$(stat -c%s "$MICROPY_BIN")"
  limit=$((APP_PARTITION_SIZE - MIN_FREE_BYTES))
  echo "micropython.bin size=$micropython_size bytes"
  echo "app partition size=$APP_PARTITION_SIZE bytes"
  echo "required max size=$limit bytes"
  if (( micropython_size >= limit )); then
    echo "[ERROR] APP_PARTITION_TOO_SMALL: micropython.bin must be smaller than app partition minus 128KB."
    exit 1
  fi
fi
