#!/usr/bin/env python3
"""Daily-ten 14 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the app sources.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261114_os.py
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
    "app_basename": "notes.txt\nhosts\nREADME.md\nlog\n4\n",
    "app_dirname": "/home/jayant\n/etc\n.\n/var\n4\n",
    "app_tee": "alpha\nbeta\ngamma\nfile: alpha\nfile: beta\nfile: gamma\n3\n",
    "app_yes": "y\ny\ny\ny\ny\n5\n",
    "app_id": "uid=1000\ngid=1000\ngroups=1000,27,100\n3\n",
    "app_whoami": "jayant\n1000\n",
    "app_uname": "MOON-OS\nmoonbox\n2.2.0\nQasida\nriscv32\n5\n",
    "app_hostname": "moonbox\n7\n",
    "app_which": "/usr/bin/ls\n/home/jayant/bin/qasida\nwhich: nope not found\n2\n",
    "app_free": ("total 8192\nused 4096\nfree 4096\nshared 512\n"
                 "buffers 256\ncached 1024\n8192\n"),
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
    print("daily-ten 14 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
