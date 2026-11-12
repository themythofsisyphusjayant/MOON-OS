# MOON-OS

A from-scratch operating system written in [Qasida](https://pypi.org/project/qasida/)
— no Linux anywhere. The goal is an OS bigger than TempleOS: its own kernel,
drivers, filesystem, shell, GUI, and networking, built on its own CPU and in
its own language.

Two things live here:

- **`examples/os/kernel_*.fg`** — real freestanding kernels for the big32 CPU:
  processes, a preemptive timer scheduler, allocators, a filesystem, a shell
  REPL, ANSI GUI windows, UART/timer drivers, and a loopback network stack.
  `kernel_unified.fg` (785 lines) puts all Phase F subsystems in one kernel
  on one memory map.
- **`examples/os/jalos.fg`** — JalOS, the earlier *simulated* teaching OS
  (1,408 lines, ~30 shell commands, VFS, users, cron, package manager). It
  runs on top of a host OS; its ideas feed the kernel, its code does not
  become kernel code. See `examples/os/README.md`.

## How to build and test

Prerequisites: Python 3.10+ and the Qasida compiler.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install qasida
```

Then, from the repo root:

```sh
python3 tests/test_kernel_idle.py      # idle task: sleep blocks (8 checks)
python3 tests/test_kernel_unified.py   # unified kernel, full shell tour
python3 tests/test_kernel_drivers.py   # UART + timer drivers
```

Each test builds its kernel freestanding for big32
(`qasida build --target big32 --freestanding`) and runs the resulting `.hex`
on the vendored Python model of the CPU (`tools/model.py`). Expected results,
verified 12 Nov 2026 with qasida 2.1.0:

| Test | Result |
| --- | --- |
| `test_kernel_idle.py` | 8/8 PASS — exact transcript `KERNA8DONE`, wake tick 8 |
| `test_kernel_unified.py` | 7/7 PASS — exact shell-tour transcript, 25 timer ticks |
| `test_kernel_drivers.py` | 6/6 PASS — exact transcript `KERNBADONE` |

### Finding the compiler

The tests resolve the compiler as:

1. `qasida` on `PATH` (the `pip install qasida` case above), else
2. `$QASIDA_BIN` — a `qasida` binary, or a `forge.py` checkout
   (a `.py` path is run via `sys.executable`), else
3. a hard error naming both options.

```sh
# Example: use a local Qasida checkout instead of the pip package
QASIDA_BIN=/path/to/forge.py python3 tests/test_kernel_idle.py
```

No RED-MOON- paths are hard-coded anywhere in this repo.

## Relationship to the other repos

- **Qasida (the language/compiler)** — the compiler this OS is written in.
  Install it with `pip install qasida`; its source lives in RED-MOON-.
  The kernels use Qasida's freestanding mode (`--freestanding`: no libc,
  own `_start`), raw memory (`peek32`/`poke32`), bitwise operators, CSR
  builtins, `ecall`, and a `trap_handler` hook — documented in
  `docs/FREESTANDING.md` (also kept in RED-MOON- as `docs/FREESTANDING.md`).
- **BIG-32 (the CPU + Verilog SOC)** — the kernels target the big32 CPU.
  The Python behavioural model of that CPU is vendored here as
  `tools/model.py` (source: BIG-32 `tools/model.py`; stdlib-only, one
  import: `sys`; see the provenance header in the file). The Verilog SOC
  itself is *not* vendored — see the SOC tests note below.
- **`tools/rebase_soc2.py`** — vendored from RED-MOON- `tools/`. It rebases
  a kernel from the model's flat 64 KB memory map to SOC2 RAM at
  `0x80000000` for the Verilog-SOC tests.

## Current state (12 Nov 2026)

- Phases A–E done: bitwise ops, raw memory, freestanding mode, CSRs +
  trap handler + `ecall`, model timer, preemptive scheduler.
- Phase F, 9 checkpoints done: bump allocator, free-list allocator, FS v1,
  FS v2 + delete, processes, shell REPL, ANSI GUI, drivers (UART + timer),
  loopback networking (SLIP). Each is a standalone kernel + test with an
  exact UART transcript on the Python big32 model.
- Idle task done 12 Nov 2026: `kernel_idle.fg` + `test_kernel_idle.py`
  (8/8 PASS, transcript `KERNA8DONE`). When no task is ready, the
  scheduler runs an idle task that waits for the next timer interrupt,
  so `sleep()` actually blocks instead of resuming immediately.
- Next: adopt the idle task into `kernel_unified.fg` (its docstring still
  carries the old "no idle task yet" limitation).
- Full history: `docs/PROGRESS.md`.

### Honest limits

- Not bootable on real hardware yet — kernels are verified on the Python
  big32 model (and, for the SOC tests, on the Verilog SOC simulation).
- 2 child slots only in the unified kernel (a third stack would grow
  through kernel regions).
- No persistence (the VFS lives in RAM).
- The unified kernel has no idle task yet (see "Next" above).

### The 9 SOC tests are not standalone

`test_kernel_fb.py`, `test_kernel_finder.py`, `test_kernel_full.py`,
`test_kernel_mac.py`, `test_kernel_mac_int.py`, `test_kernel_netdev.py`,
`test_kernel_pix.py`, `test_kernel_term.py`, and
`test_kernel_uart16550_soc2.py` additionally need a BIG-32 checkout
(`src/big32_core_pipe.v`, `src/big32_soc2.v`), the rx-proof testbenches
(`tb_*.v`), and `iverilog` on `PATH`. Point at them with:

```sh
BIG32_DIR=/path/to/big32 RX_PROOF_DIR=/path/to/rx-proof python3 tests/test_kernel_fb.py
```

Without those, they print `SKIP SOC2 test ...` and exit 0 — a loud skip,
not a pass. The other 117 tests are fully standalone: compiler + this repo
is all they need.

## Layout

```text
examples/os/     169 .fg kernel/app sources + JalOS README
tests/           126 test_kernel_*.py (adapted to resolve qasida from PATH)
tools/           model.py (vendored big32 model), rebase_soc2.py (vendored)
docs/            FREESTANDING.md (freestanding-mode reference)
                 PROGRESS.md (phase log, kept with history)
```
