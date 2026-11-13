#!/usr/bin/env python3
"""End-to-end test for the idle task inside the unified kernel.

The unified kernel (examples/os/kernel_unified.fg) integrates the
idle task from kernel_idle.fg: idle is a real spawned task in
slot 1 (state 5, pid recorded at 0x804C), children use slot 2
only, and sleep() really blocks — when no task is ready and a
sleeper exists the scheduler runs the idle task until the next
timer interrupt wakes the sleeper.

The shell's `z` command spawns a task that prints 'Z' plus the
tick count, sleeps 5 ticks, then prints 'K' plus the tick count
at wake time. The test feeds `z`, `w` (wait for the sleeper to
exit), `q`, and asserts the wake tick is at least 5 ticks after
the start tick. Discrimination against the old behaviour: with
the pre-integration immediate resume the task would have
printed its wake tick at ~the start tick (difference ~0), so a
difference >= 5 cannot pass on the old code. Also asserts the
kernel halts, final states [running, idle, done, free], idle
pid 1, and the sleeper in slot 2. Exits 0 only if every test
passes.
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Compiler resolution for this standalone repo (see README.md):
#   1. `qasida` on PATH (e.g. `pip install qasida`), else
#   2. $QASIDA_BIN: a `qasida` binary, or a `forge.py` checkout
#      (a .py path is run via sys.executable), else
#   3. a hard error naming both options. No RED-MOON- paths hard-coded.
import shutil as _shutil


def _qasida_cmd():
    found = _shutil.which("qasida")
    if found:
        return [found]
    env = os.environ.get("QASIDA_BIN")
    if env:
        return [sys.executable, env] if env.endswith(".py") else [env]
    raise SystemExit(
        "qasida compiler not found: `pip install qasida` or set "
        "QASIDA_BIN to a qasida binary / forge.py path (see README.md).")


QASIDA = _qasida_cmd()
MODEL = os.path.join(ROOT, "tools", "model.py")
FAILURES = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        FAILURES.append(name)


def word(dmem, a):
    return (dmem[a] | (dmem[a + 1] << 8) |
            (dmem[a + 2] << 16) | (dmem[a + 3] << 24))


def main():
    print("unified kernel idle task: sleep blocks via idle (big32 model)")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "kern_uni_idle")
        r = subprocess.run(QASIDA + ["build", "--target", "big32",
                                    "--freestanding", "-o", out,
                                    "examples/os/kernel_unified.fg"],
                           capture_output=True, text=True, cwd=ROOT)
        check("builds freestanding big32", r.returncode == 0, r.stderr[-200:])
        spec = importlib.util.spec_from_file_location("big32model", MODEL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.run(out + ".hex",
                      input_bytes=b"z\nw\nq\n")
        uart = res["uart"].decode("utf-8", "replace")
        m = re.search(r"Z(\d+).*K(\d+)", uart, re.DOTALL)
        start = int(m.group(1)) if m else -1
        wake = int(m.group(2)) if m else -1
        check("sleep demo ran (Z<start>...K<wake>)", m is not None, repr(uart))
        check("wake tick >= 5 after start tick", wake - start >= 5,
              f"start={start} wake={wake}")
        check("wait saw exit code 0", "W0" in uart, repr(uart))
        check("shell quit cleanly", uart.endswith("BYE\n"), repr(uart))
        check("halts", res["halted"] is True)
        d = res["dmem"]
        check("final states [running, idle, done, free]",
              [word(d, 0x8000 + 16 * i) for i in range(4)] == [2, 5, 3, 0])
        check("idle pid is slot 1", word(d, 0x804C) == 1,
              str(word(d, 0x804C)))
        check("sleeper pid is slot 2", word(d, 0x8044) == 2,
              str(word(d, 0x8044)))
        check("timer kept ticking to the end", word(d, 0x8048) >= 5,
              str(word(d, 0x8048)))
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
