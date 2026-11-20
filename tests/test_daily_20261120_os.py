#!/usr/bin/env python3
"""Daily-ten 20 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the intended fixed inputs, with an
independent Python replica (/tmp/daily20/expected.json).

The OS-chain kernel slice (lifetime allocator v2 into the
unified kernel) is NOT in this file: it is BLOCKED (see the
day summary) — the adopted kernel builds to 4319 words, over
the Python big32 model's 4096-word instruction memory, so the
model wraps PC to 0 and the kernel restarts in a loop. Do NOT
re-attempt; it needs a coordinator decision.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261120_os.py
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
    "app_dmesg": "0\n12\n45\n3\n",
    "app_lspci": "512\n768\n256\n3\n",
    "app_lsblk": "512\n1024\n2048\n3584\n3\n",
    "app_pstree": "1\n42\n1234\n1277\n3\n",
    "app_lsof": "1001\n1002\n1003\n3\n",
    "app_printenv": "12\n6\n9\n3\n",
    "app_nproc": "4\n2\n8\n",
    "app_hostid": "8323585\n585\n1\n",
    "app_time": "120\n80\n40\n120\n",
    "app_size": "4096\n512\n256\n4864\n",
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
    print("daily-ten 20 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
