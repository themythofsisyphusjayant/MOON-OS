#!/usr/bin/env python3
"""End-to-end test for Phase F checkpoint 1: bump allocator kernel.

An allocator needs no pointers in Qasida: addresses are plain
ints, peek32/poke32 are the read/write. The heap is [0xA000,
0xC000), the bump pointer lives in RAM scratch 0x8040.
alloc(size) aligns up to 4, fails with -1 past the heap end, else
advances the bump pointer and returns the block. free is a
deliberate no-op here (a free-list is checkpoint 2).

The kernel (examples/os/kernel_alloc.fg) allocates three blocks,
writes patterns through poke32, reads them back through peek32,
prints K per verified block, allocates past the end (must fail
with -1) for another K, then DONE and halts. Output is poke32
UART bytes only — freestanding rejects print.

Expects the exact transcript KERNKKKKDONE, halted, and the
patterns present in the model heap. Exits 0 only if every test
passes.
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


def word(dmem, a):
    return (dmem[a] | (dmem[a + 1] << 8) |
            (dmem[a + 2] << 16) | (dmem[a + 3] << 24))


def main():
    print("bump allocator (big32 model)")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "kern_alloc")
        r = subprocess.run(QASIDA + ["build", "--target", "big32",
                                    "--freestanding", "-o", out,
                                    "examples/os/kernel_alloc.fg"],
                           capture_output=True, text=True, cwd=ROOT)
        check("builds freestanding big32", r.returncode == 0, r.stderr[-200:])
        spec = importlib.util.spec_from_file_location("big32model", MODEL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.run(out + ".hex")
        uart = res["uart"].decode("utf-8", "replace")
        check("exact transcript KERNKKKKDONE", uart == "KERNKKKKDONE", uart)
        check("halts", res["halted"] is True)
        d = res["dmem"]
        check("block1 pattern intact",
              word(d, 0xA000) == 111 and word(d, 0xA00C) == 444)
        check("block2 aligned + intact", word(d, 0xA010) == 77)
        check("block3 intact", word(d, 0xA018) == 55)
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
