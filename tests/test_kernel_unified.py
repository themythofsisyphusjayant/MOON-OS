#!/usr/bin/env python3
"""End-to-end test for integration: one unified kernel.

Every Phase F subsystem in a single program on a single
memory map: processes + preemptive timer (checkpoints 5+8),
bump allocator (1), filesystem v2 (4), shell REPL (6), ANSI
GUI windows (7), loopback network stack (9), plus the idle
task in slot 1 (state 5) integrated 13 Nov 2026: only 1 child
slot fits (slot 2), and sleep() now really blocks — when no
task is ready and a sleeper exists the scheduler runs the
idle task until the next timer interrupt wakes the sleeper.

The kernel (examples/os/kernel_unified.fg) is fed one line
per shell command: h, p, s, w, m, f, g, n, q. Expects the
exact transcript — note HI> w rather than the shell
checkpoint's H> w / IW0: a timer tick fired between the
child's yield and the shell's next print, bouncing control
back to the child for its final I, which is preemption and
cooperation interleaving as designed — halted, main
running, the child done, timer ticks fired, the heap bump
advanced by exactly one 16-byte alloc, and net stats
4/3/1. Exits 0 only if every test passes.
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

EXPECTED = ("KERN\n"
            "> h\n"
            "h p s w m f g n q\n"
            "> p\n"
            "P0:2 P1:5 P2:0 P3:0 \n"
            "> s\n"
            "HI> w\n"
            "W0\n"
            "> m\n"
            "M8400\n"
            "> f\n"
            "F\n"
            "> g\n"
            "\x1b[2J\x1b[H"
            "\x1b[2;2H+A-------+\x1b[3;2H|        |\x1b[4;2H|        |"
            "\x1b[5;2H+--------+"
            "\x1b[4;5H+B-------+\x1b[5;5H|        |\x1b[6;5H|        |"
            "\x1b[7;5H+--------+"
            "\x1b[2;2H+A-------+\x1b[3;2H|        |\x1b[4;2H|        |"
            "\x1b[5;2H+--------+\n"
            "> n\n"
            "PONG\n"
            "S4R3D1\n"
            "> q\n"
            "BYE\n")


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        FAILURES.append(name)


def word(dmem, a):
    return (dmem[a] | (dmem[a + 1] << 8) |
            (dmem[a + 2] << 16) | (dmem[a + 3] << 24))


def main():
    print("unified kernel (big32 model)")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "kern_uni")
        r = subprocess.run(QASIDA + ["build", "--target", "big32",
                                    "--freestanding", "-o", out,
                                    "examples/os/kernel_unified.fg"],
                           capture_output=True, text=True, cwd=ROOT)
        check("builds freestanding big32", r.returncode == 0, r.stderr[-200:])
        spec = importlib.util.spec_from_file_location("big32model", MODEL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.run(out + ".hex",
                      input_bytes=b"h\np\ns\nw\nm\nf\ng\nn\nq\n")
        uart = res["uart"].decode("utf-8", "replace")
        check("exact transcript", uart == EXPECTED, repr(uart))
        check("halts", res["halted"] is True)
        d = res["dmem"]
        check("final states [running, idle, done, free]",
              [word(d, 0x8000 + 16 * i) for i in range(4)] == [2, 5, 3, 0])
        check("timer fired repeatedly", word(d, 0x8048) >= 10,
              str(word(d, 0x8048)))
        check("heap bump advanced one alloc", word(d, 0x8050) == 33808)
        check("net stats 4/3/1",
              word(d, 0x82F8) == 4 and word(d, 0x82FC) == 3 and
              word(d, 0x8300) == 1)
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
