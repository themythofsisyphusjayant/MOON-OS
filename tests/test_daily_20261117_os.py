#!/usr/bin/env python3
"""Daily-ten 17 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the app sources.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261117_os.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORGE_PY = os.environ.get(
    "FORGE_PY", os.path.expanduser("~/workspace/forge-v2/forge.py"))
FORGE = [sys.executable, FORGE_PY]
FAILURES = []

EXPECTED = {
    "app_ln": "readme.txt\n1001\nreadme_link.txt\n1001\nnotes.txt\n1002\n3\n",
    "app_rmdir": "empty1\nremoved\ndocs\nnot empty\nempty2\nremoved\n2\n",
    "app_chown": "a.txt\njayant\nroot\nb.txt\njayant\nroot\n2\n",
    "app_who": "jayant\ntty1\n09:00\naman\ntty2\n09:13\n2\n",
    "app_wall": "Broadcast message from root:\nsystem reboot at 10:00\n2\n",
    "app_clear": "\n\n\ncleared\n3\n",
    "app_stty": "speed 9600 baud\nrows\n24\ncols\n80\n1920\n3\n",
    "app_factor": "2\n2\n3\n5\n4\n",
    "app_expr": "11\n3\n2\n7\n4\n",
    "app_test": "1\n1\n0\n1\n4\n",
}


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        FAILURES.append(name)


def run_one(name, expected, env_extra):
    path = os.path.join(ROOT, "examples", "os", name + ".fg")
    env = dict(os.environ)
    env.update(env_extra)
    try:
        r = subprocess.run(FORGE + ["run", path], capture_output=True,
                           text=True, cwd=ROOT, env=env, timeout=180)
    except subprocess.TimeoutExpired:
        check(f"{name} runs", False, "TIMEOUT after 180s")
        return
    check(f"{name} runs rc=0", r.returncode == 0, r.stderr[-200:])
    check(f"{name} exact stdout", r.stdout == expected,
          "" if r.stdout == expected else f"got: {r.stdout!r}")


def main():
    print("daily-ten 17 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
