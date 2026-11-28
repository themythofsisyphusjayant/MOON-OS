#!/usr/bin/env python3
"""Daily-ten 28 Nov 2026 — OS track (10 native apps).

Runs each app under `forge.py run` with BOTH compilers (hosted
default + QASIDA_COMPILER=python) and compares stdout to the
expected transcript exactly. Expected values were hand-computed
BEFORE the first run, from the intended fixed inputs, and each
app was verified individually by the coordinator first.

The OS-chain kernel slice (lifetime allocator v2 into the
unified kernel) is NOT in this file: it is BLOCKED — the adopted
kernel builds to 4319 words, over the Python big32 model's
4096-word instruction memory (measured 20 Nov 2026;
kernel_unified.fg unchanged since 19 Nov, unified alone builds
to 3825 words now, so the block stands). Terminal in a window
and the Notes app are already in the tree (kernel_term.fg,
kernel_notes.fg); the standalone lifetime2 kernel passes 5/5
on the model. See coordinator plan
~/workspace/blackmoon-iso/daily-20261128/PLAN.md.

Compiler resolution (see README.md): $FORGE_PY (a forge.py
checkout) or the default ~/workspace/forge-v2/forge.py.

Usage:
  python3 tests/test_daily_20261128_os.py
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
    "app_chgrp": "report.txt\nstaff\nnotes.md\nstaff\n2\n1\n",
    "app_pgrep": "42\n256\n2\n",
    "app_pidof": "42\n137\n256\n3\n",
    "app_killall": "101 TERM\n137 TERM\n142 TERM\n3\n2\n",
    "app_w": ("125\njayant tty1 09:00\naman tty2 09:13\n"
              "teju tty3 10:25\n12\n45\n8\n3\n"),
    "app_finger": ("Login: jayant\nName: Jayant Dubey\n"
                   "Directory: /home/jayant\nShell: /bin/bash\n"
                   "Total users: 3\nBash users: 2\n"),
    "app_logger": "1\n6\n14\n4\n3\n35\n3\n5\n29\n3\n78\n",
    "app_iostat": ("sda 51200 25600 76800\nsdb 10240 5120 15360\n"
                   "nvme0n1 204800 102400 307200\n266240\n133120\n3\n"),
    "app_lscpu": "big32\n1\n4\n2\n8\n32\n256\n288\n",
    "app_blkid": ('/dev/sda1: UUID="a1b2-c3d4-e5f6" TYPE="ext4"\n'
                  '/dev/sdb1: UUID="7890-abcd-1234" TYPE="xfs"\n'
                  '/dev/nvme0n1p1: UUID="5678-ef90-2468" TYPE="vfat"\n'
                  '3\n1\n'),
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
    print("daily-ten 28 Nov 2026 — OS track (10 apps x 2 compilers)")
    for name, expected in EXPECTED.items():
        print(f"{name} (hosted):")
        run_one(name, expected, {})
        print(f"{name} (python):")
        run_one(name, expected, {"QASIDA_COMPILER": "python"})
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
