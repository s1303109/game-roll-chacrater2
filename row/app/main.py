import gc
import os
import sys
import time

START_DELAY_MS = 1200
RESTART_DELAY_MS = 1200
APP_PATHS = ("/sd/app", "/app", "/remote/app", "/")


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _ensure_app_path():
    for base in APP_PATHS:
        if _exists(base):
            if base not in sys.path:
                sys.path.insert(0, base)
            else:
                # Keep selected app base as highest priority.
                sys.path.remove(base)
                sys.path.insert(0, base)
            return base
    return ""


def _mount_sd():
    try:
        from sd_host import mount_sd
    except Exception:
        return
    try:
        mount_sd("/sd", return_ok=True)
    except Exception:
        return


def _clear_game_modules():
    for name in list(sys.modules):
        if name == "game_mvp" or name.startswith("game_mvp."):
            del sys.modules[name]


def main():
    _mount_sd()
    app_base = _ensure_app_path()
    if app_base:
        print("main_app_base:", app_base)
    time.sleep_ms(START_DELAY_MS)
    while True:
        try:
            gc.collect()
            _clear_game_modules()
            import game_mvp
            return
        except Exception as err:
            print("main_error:", err)
            sys.print_exception(err)
            time.sleep_ms(RESTART_DELAY_MS)
            gc.collect()


main()
