#!/usr/bin/env python3
"""16550 UART driver kernel test (big32 model).

Verifies the divisor computation and transcript exactly. The 16550 register
writes themselves are NOT verified by this test: the small model has no
16550 (its stores wrap into low dmem harmlessly), so hardware verification
belongs to a later SOC2 Verilog run, not this model test.
Expects "9600=12", "19200=6", "38400=3", "115200=1", "DONE", halted.
"""
import importlib.util
import os
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


def main():
    print("16550 uart driver (big32 model)")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "kern_uart16550")
        r = subprocess.run(QASIDA + ["build", "--target", "big32",
                                    "--freestanding", "-o", out,
                                    "examples/os/kernel_uart16550.fg"],
                           capture_output=True, text=True, cwd=ROOT)
        check("builds freestanding big32", r.returncode == 0, r.stderr[-300:])
        if r.returncode != 0:
            print("FAILED")
            return 1
        spec = importlib.util.spec_from_file_location("big32model", MODEL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.run(out + ".hex")
        uart = res["uart"].decode("utf-8", "replace")
        check("halts", res["halted"] is True)
        check("exact transcript",
              uart == "9600=12\n19200=6\n38400=3\n115200=1\nDONE\n", repr(uart))
    if FAILURES:
        print("FAILED:", FAILURES)
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
