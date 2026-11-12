#!/usr/bin/env python3
"""SBI-style dispatch demo kernel test (big32 model).

Fresh Qasida reimplementation of the dispatch pattern Ghidra decoded from
the big32 SBI firmware: EID compare-and-branch, Base FIDs from a0, TIME from
mtime, unknown EID -> -2. Expects transcript lines "2", "7", "<digits>",
"-2", "DONE" (the mtime line is timing-dependent, so only its shape is
checked), and halted.
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
    print("sbi dispatch demo (big32 model)")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "kern_sbi_demo")
        r = subprocess.run(QASIDA + ["build", "--target", "big32",
                                    "--freestanding", "-o", out,
                                    "examples/os/kernel_sbi_demo.fg"],
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
        lines = uart.split("\n")
        check("halts", res["halted"] is True)
        check("spec version line is 2", len(lines) > 0 and lines[0] == "2", repr(uart))
        check("impl id line is 7", len(lines) > 1 and lines[1] == "7", repr(uart))
        check("time line is digits", len(lines) > 2 and lines[2].isdigit(), repr(uart))
        check("unknown eid line is -2", len(lines) > 3 and lines[3] == "-2", repr(uart))
        check("DONE line", len(lines) > 4 and lines[4] == "DONE", repr(uart))
    if FAILURES:
        print("FAILED:", FAILURES)
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
