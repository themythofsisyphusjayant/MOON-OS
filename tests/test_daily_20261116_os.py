#!/usr/bin/env python3
"""Daily-ten 16 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the app sources.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261116_os.py
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
    "app_awk": "jayant staff\n3\naman dev\n3\n2\n",
    "app_sed": "bar bar bar\n2\nno match here\n0\n2\n",
    "app_cmp": "3\n99 100\n0\n1\n",
    "app_pr": "Page 1\none\ntwo\nPage 2\nthree\nfour\nPage 3\nfive\n3\n",
    "app_fmt": "pack my box with\nfive dozen liquor\njugs\n3\n",
    "app_unexpand": "\ta\n\t\tb\n  c\n3\n",
    "app_tsort": "a\nb\nc\n3\n",
    "app_cksum": "210\n154\n364\n2\n",
    "app_base64": "SGkh\nTWFu\n2\n",
    "app_hexdump": "0 48\n1 69\n2 21\n3\n",
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
    print("daily-ten 16 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
