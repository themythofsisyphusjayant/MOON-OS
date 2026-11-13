#!/usr/bin/env python3
"""Daily-ten 13 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the app sources.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261113_os.py
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
    "app_touch": "notes.txt 100\ntodo.fg 999\nREADME.md 300\nnew.txt 999\n4\n",
    "app_mkdir": "mkdir: src exists\nsrc\ndocs\ntests\n3\n",
    "app_rm": "rm: x.txt not found\na.txt\nc.txt\nd.txt\n3\n",
    "app_mv": "mv: gone.txt not found\nnew.txt\nkeep.txt\ndata.csv\n3\n",
    "app_more": ("one\ntwo\nthree\n--More--\nfour\nfive\nsix\n"
                 "--More--\nseven\n7\n"),
    "app_cut": "dev\nops\nqa\n1001\n1002\n1003\n",
    "app_tr": "h2ll4 w4rld\nq1s3d1\n6\n",
    "app_comm": "fig\nkiwi\n2\n",
    "app_diff": "2\nbeta\nbeta2\n4\ndelta\nepsilon\n2\n",
    "app_cal": ("November 2026\nSu Mo Tu We Th Fr Sa\n"
                "1 2 3 4 5 6 7\n8 9 10 11 12 13 14\n"
                "15 16 17 18 19 20 21\n22 23 24 25 26 27 28\n29 30\n30\n"),
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
    print("daily-ten 13 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
