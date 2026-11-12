#!/usr/bin/env python3
"""End-to-end test for Phase F checkpoint 9: networking.

Loopback stack: SLIP framing (RFC 1055), UDP-inspired fixed
packets [dst, src, len, payload, checksum], echo service on
port 7 (ping payload 1 -> pong payload 2). The wire is an
in-memory loopback buffer (no NIC exists in the model or the
Verilog); bytes are stored as words, linear positions.

The kernel (examples/os/kernel_net.fg) sends a packet and
corrupts its payload in transit (receive must drop it on a
checksum mismatch), sends a packet with payload 192
(exercising the SLIP ESC path end to end), then runs the
ping flow and prints PONG, then stats, then DONE. Expects
the exact transcript KERN / PONG / S4R3D1 / DONE, halted,
all 29 framed bytes consumed, and sent 4 / recv 3 /
dropped 1. Exits 0 only if every test passes.
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

EXPECTED = "KERN\nPONG\nS4R3D1\nDONE\n"


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        FAILURES.append(name)


def word(dmem, a):
    return (dmem[a] | (dmem[a + 1] << 8) |
            (dmem[a + 2] << 16) | (dmem[a + 3] << 24))


def main():
    print("networking loopback stack (big32 model)")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "kern_net")
        r = subprocess.run(QASIDA + ["build", "--target", "big32",
                                    "--freestanding", "-o", out,
                                    "examples/os/kernel_net.fg"],
                           capture_output=True, text=True, cwd=ROOT)
        check("builds freestanding big32", r.returncode == 0, r.stderr[-200:])
        spec = importlib.util.spec_from_file_location("big32model", MODEL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.run(out + ".hex")
        uart = res["uart"].decode("utf-8", "replace")
        check("exact transcript", uart == EXPECTED, repr(uart))
        check("halts", res["halted"] is True)
        d = res["dmem"]
        check("all bytes consumed",
              word(d, 0x8050) == 29 and word(d, 0x8054) == 29,
              f"write {word(d, 0x8050)} read {word(d, 0x8054)}")
        check("stats sent 4 recv 3 dropped 1",
              word(d, 0x8060) == 4 and word(d, 0x8064) == 3 and
              word(d, 0x8068) == 1)
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
