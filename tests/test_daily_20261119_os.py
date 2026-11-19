#!/usr/bin/env python3
"""Daily-ten 19 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the app sources, with an independent
Python replica (/tmp/daily19/expected.json).

The OS-chain kernel slice (lifetime allocator v2 into the
unified kernel) is NOT in this file: it is blocked (see the
day summary) — the adopted kernel builds to 4319 words, over
the Python big32 model's 4096-word instruction memory, so the
model wraps PC to 0 and the kernel restarts in a loop. The
kernel files were reverted to the verified baseline, and
today's 10 items are all native apps.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261119_os.py
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
    "app_dd": "3\n3\n1536\n3\n",
    "app_nohup": "1234\n1\n0\n3\n",
    "app_sync": "3\n3\n0\n3\n",
    "app_tar": "100\n200\n300\n600\n3\n",
    "app_shuf": "20\n30\n40\n10\n4\n",
    "app_groups": "wheel\ndev\naudio\n3\n",
    "app_logname": "jayant\n6\n1\n",
    "app_unlink": "tmp.txt\n1\n2\n",
    "app_renice": "1234\n0\n5\n5\n",
    "app_vmstat": "1\n0\n1024\n0\n10\n20\n6\n",
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
    print("daily-ten 19 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
