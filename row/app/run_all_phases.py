import gc
import os
import sys


def _run_script(path):
    print("\n=== run:", path, "===")
    script_dir = path.rsplit("/", 1)[0]
    added = False
    if script_dir and script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        added = True
    with open(path, "r") as f:
        code = f.read()
    try:
        glb = {"__name__": "__main__", "__file__": path}
        exec(code, glb)
        gc.collect()
        print("=== ok:", path, "===")
    finally:
        if added:
            try:
                sys.path.remove(script_dir)
            except ValueError:
                pass


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def main():
    base = "/remote/app"
    if not _exists(base):
        base = "/app"

    scripts = [
        "test_sd.py",
        "test_sprite.py",
        "test_tiles.py",
        "game_mvp.py",
        "validate_full.py",
    ]

    # Optional: if remote assets exist, copy to SD first.
    copy_script = base + "/copy_assets_to_sd.py"
    if _exists("/remote/assets/out/map.json") and _exists(copy_script):
        _run_script(copy_script)

    for name in scripts:
        _run_script(base + "/" + name)

    print("\nAll phases done.")


try:
    main()
except Exception as e:
    print("\nrun_all_phases failed:", e)
    sys.print_exception(e)
    raise
