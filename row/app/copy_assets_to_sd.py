import os
import time
from sd_host import mount_sd

SRC_BASE = "/remote/assets/out"
DST_BASE = "/sd/out"
CHUNK = 4096
SD_FREQS = (8_000_000, 4_000_000, 12_000_000, 20_000_000)
COPY_RETRIES = 3
FILES = ("map.json", "tilemap.bin", "tileset.bin", "collision.bin", "player_sheet.rgb565")


def ensure_sd():
    for freq in SD_FREQS:
        try:
            if mount_sd("/sd", freq=freq, return_ok=True):
                return
        except OSError:
            pass
    raise RuntimeError("SD_MOUNT_FAIL")


def ensure_dir(path):
    parts = [p for p in path.split("/") if p]
    cur = ""
    for p in parts:
        cur += "/" + p
        try:
            os.stat(cur)
        except OSError:
            os.mkdir(cur)


def _file_size(path):
    try:
        return os.stat(path)[6]
    except OSError:
        return -1


def copy_file(src, dst):
    src_size = _file_size(src)
    last_err = None
    for _ in range(COPY_RETRIES):
        tmp = dst + ".tmp"
        try:
            os.remove(tmp)
        except OSError:
            pass
        try:
            with open(src, "rb") as fin, open(tmp, "wb") as fout:
                while True:
                    b = fin.read(CHUNK)
                    if not b:
                        break
                    fout.write(b)
            dst_size = _file_size(tmp)
            if src_size >= 0 and dst_size != src_size:
                raise RuntimeError("COPY_SIZE_MISMATCH")
            try:
                os.remove(dst)
            except OSError:
                pass
            os.rename(tmp, dst)
            return
        except Exception as err:
            last_err = err
            try:
                os.remove(tmp)
            except OSError:
                pass
            time.sleep_ms(80)
    raise last_err


ensure_sd()
ensure_dir(DST_BASE)

for name in FILES:
    src = SRC_BASE + "/" + name
    dst = DST_BASE + "/" + name
    copy_file(src, dst)
    print("copied", name)

print("copy done")
