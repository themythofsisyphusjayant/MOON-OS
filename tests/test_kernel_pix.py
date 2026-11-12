#!/usr/bin/env python3
"""Pixel framebuffer kernel test (SOC2 simulation).

Builds examples/os/kernel_pix.fg for big32 freestanding with
the SOC2 stack top, compiles the pixel testbench against
the SOC2 sources, runs it, and checks the verdict plus the
UART transcript.

The kernel uses no RAM scratch, so no rebase step is
needed (all its literals are either small or MMIO).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
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
PROOF = os.environ.get("RX_PROOF_DIR", "")
BIG32 = os.environ.get("BIG32_DIR", "")
TMP = "/tmp"


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def main():
    # SOC2 tests are NOT standalone: they need a BIG-32 checkout
    # (src/big32_core_pipe.v + src/big32_soc2.v), the rx-proof
    # testbenches (tb_*.v), and iverilog. Skip loudly instead of
    # failing on a missing path. See README.md.
    if not BIG32 or not PROOF or not _shutil.which("iverilog"):
        print("  SKIP SOC2 test: set BIG32_DIR and RX_PROOF_DIR and "
              "install iverilog (see README.md).")
        return 0
    failures = []

    def check(name, ok, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'} {name} {detail}")
        if not ok:
            failures.append(name)

    b = sh([*_qasida_cmd(), "build",
            "--target", "big32", "--freestanding",
            "--stack-top", "0x800F0000",
            "-o", os.path.join(TMP, "kern_pix"),
            os.path.join(ROOT, "examples/os/kernel_pix.fg")])
    check("builds freestanding big32", b.returncode == 0, b.stderr[-200:])

    c = sh(["iverilog", "-o", os.path.join(TMP, "tb_pix.vvp"),
            os.path.join(BIG32, "src/big32_core_pipe.v"),
            os.path.join(BIG32, "src/big32_soc2.v"),
            os.path.join(TMP, "tb_pix.v")])
    check("SOC2 + testbench compile", c.returncode == 0, c.stderr[-200:])

    r = sh(["vvp", os.path.join(TMP, "tb_pix.vvp"),
            f"+HEX={os.path.join(TMP, 'kern_pix.hex')}",
            f"+TXOUT={os.path.join(TMP, 'pix_tx.txt')}"],
           timeout=900)
    out = r.stdout + r.stderr
    verdict = [ln for ln in out.splitlines() if "PIX PASS" in ln or "PIX FAIL" in ln]
    check("pixel verdict PIX PASS", bool(verdict) and "PIX PASS" in verdict[0], str(verdict))
    try:
        tx = open(os.path.join(TMP, "pix_tx.txt"), "rb").read().decode("ascii")
    except OSError:
        tx = ""
    check("exact transcript 'KERN\\nDONE\\n'", tx == "KERN\nDONE\n", repr(tx))
    print(f"\n{len(failures)} failure(s): {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
