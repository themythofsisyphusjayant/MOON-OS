#!/usr/bin/env python3
"""Daily-ten 15 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the app sources.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261115_os.py
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
    "app_expand": "a   b\nab  c\nabcd    e\n3\n",
    "app_fold": "the quick\nbrown fox\njumps over\n3\n",
    "app_join": "jayant:/bin/bash\naman:/bin/zsh\n2\n",
    "app_paste": "alpha:1\nbeta:2\ngamma:3\n3\n",
    "app_split": "red\ngreen\nblue\nyellow\n4\n",
    "app_od": "72 110\n105 151\n33 41\n3\n",
    "app_stat": ("notes.txt 4096 644\nphoto.png 204800 644\n"
                 "data.bin 512 600\n209408\n"),
    "app_tty": "/dev/tty1\n0\n2\n",
    "app_cpuinfo": "Qasida RV32\n4\n100\n256\n400\n",
    "app_lsmod": ("virtio_blk 8192 1\next4 40960 2\n"
                  "qasida_net 16384 0\n65536\n3\n"),
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
    print("daily-ten 15 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
