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


def _script_dir():
    path = globals().get("__file__", "run_all_phases.py")
    if "/" not in path:
        return "."
    return path.rsplit("/", 1)[0]


def main():
    base = _script_dir()
    scripts = [
        "test_sd.py",
        "test_sprite.py",
        "test_tiles.py",
        "validate_full.py",
    ]

    for name in scripts:
        path = base + "/" + name
        if not _exists(path):
            raise OSError("missing script: " + path)
        _run_script(path)

    print("\nrun_all_phases does not launch game_mvp.main(); use reset or import main to boot the cartridge.")
    print("All validation phases done.")


try:
    main()
except Exception as e:
    print("\nrun_all_phases failed:", e)
    sys.print_exception(e)
    raise
