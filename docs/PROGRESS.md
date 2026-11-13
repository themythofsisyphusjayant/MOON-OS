# From-scratch OS — progress log (coordinator)

## State assessment — 12 Nov 2026 ~12:50 IST (verified from docs + tree)

### Correction to the brief's expectation
The brief expected the next slice to be "UART hello, then timer tick, then
the scheduler" on the big32 simulator. **All three are DONE (Phase E,
27 Oct 2026):** UART hello, timer tick (model CLINT, `KERNTTTTTDONE`),
preemptive round-robin scheduler (`kernel_sched.fg`, 907 A + 981 B,
19 switches, 20 ticks). The real next slice is below.

### What exists (all recorded as done 27–30 Oct 2026, docs/FREESTANDING.md)
- Phases A–E: bitwise ops, peek32/poke32, freestanding mode, CSRs +
  trap handler + ecall/ecall3, model timer, preemptive scheduler.
- Phase F (9 checkpoints): bump allocator, free-list allocator, FS v1,
  FS v2 + delete, processes, shell REPL, ANSI GUI, drivers (UART+timer),
  loopback networking (SLIP). Each a standalone kernel + test, exact
  UART transcripts on the Python big32 model.
- Integration: `examples/os/kernel_unified.fg` (866 lines) — all Phase F
  subsystems in one kernel, one memory map; `tests/test_kernel_unified.py`
  (shell tour h/p/s/w/m/f/g/n/q, 27 ticks, halted).
- Hardware frontiers: UART RX FIFO in SOC2, unified kernel rebased and
  run on Verilog SOC (tb_shell.v, 45,461 cycles), real serial packet
  device, text VRAM (80x25), pixel VRAM (320x200, then 640x480) + 8x8
  font, macOS-look static desktop, INTERACTIVE desktop (pointer, drag,
  close, live mtime clock), Finder app (FS-backed file list), Terminal
  in a window (16x38 text buffer, first-char shell dispatch),
  lifetime-ordered allocator v2 (QAIRT borrow), SBI dispatch demo,
  16550 UART driver kernel.
- big32 boots unmodified Linux 6.6.52 to a shell prompt (Steps 29–31,
  commit 6ddf7e07). SOC2 has CLINT, UART RX FIFO, net device, text
  VRAM, pixel VRAM, pointer device.
- JalOS (`examples/os/jalos.fg`, 1408 lines) stays the SIMULATED
  teaching prototype — its ideas feed the kernel, its code does not
  become kernel code.

### Honest limits carried over (from the docs)
- ~~No idle task yet~~ — FIXED 13 Nov 2026 (Slice 2 below): the idle
  task is integrated into `kernel_unified.fg` (slot 1, state 5, pid
  at 0x804C); sleep() now really blocks. The standalone
  `kernel_idle.fg` keeps the same design.
- 1 child slot only in the unified kernel (slot 2; slot 1 is the
  idle task — a third stack would grow through kernel regions).
- Palette indices only (0–9), no palette register.
- No persistence (VFS lives in RAM).
- kernel_pix / kernel_full 640-wide re-runs not yet claimed.
- SOC2 device edits stay LOCAL (BIG-32 publication belongs to the
  Linux-boot track).

### Environment state at dispatch (12 Nov ~12:50 IST)
- Remote main: 90d2f8f9 (Step 5 of the speed program).
- **iverilog NOT installed** (vanished in a VM restart) — Verilog SOC
  sims cannot run until it is restored; Python big32 model sims work.
  Slices must be model-verifiable; SOC2 re-verification is a later
  step, not a blocker.
- **Step 6 (speed program, incremental compilation) is ACTIVE in the
  same tree** — it is rebuilding bin/qasida-hosted right now. Do NOT
  touch compiler sources. Kernel builds go through `forge.py build
  --target big32 --freestanding` (hosted defers big32; establish the
  actual dispatch from the code and record which compiler + md5 built
  the kernel; use QASIDA_COMPILER=python for determinism while Step 6
  rebuilds, and say so plainly).
- No sims running at dispatch time.

## Slice 2: IDLE TASK IN THE UNIFIED KERNEL — DONE 13 Nov 2026
- Why: the most-named known limitation (three places in the docs);
  Slice 1 proved the design standalone (`kernel_idle.fg`, 12 Nov);
  the unified kernel still carried the old limitation in its
  docstring, so sleep() in the integrated kernel degraded to an
  immediate resume instead of blocking.
- What: adopt the idle task into `kernel_unified.fg` — same three
  no-ready paths (sleep/yield/exit switch to idle when a sleeper
  exists), idle in slot 1 (state 5, pid at 0x804C), children in
  slot 2 only (spawn scan starts at s=2 once the idle pid is
  recorded; the first spawn takes slot 1). New shell command `z`:
  spawn a task that prints its start tick, sleeps 5 ticks, then
  prints its wake tick. Slice 1's standalone kernel is recorded
  below, unchanged.
- Files: `examples/os/kernel_unified.fg` (785 → 866 lines),
  `tests/test_kernel_unified.py` (expectations changed only where
  the integration deliberately changes them: `p` line P1:5, final
  states [2,5,3,0]), new `tests/test_kernel_unified_idle.py`.
  `kernel_idle.fg` / `test_kernel_idle.py` untouched.
- Verified by implementer from own runs + logs (Python big32 model
  only; no SOC2 — iverilog absent), Qasida 2.2.0 venv:
  `test_kernel_unified.py` **7/7 PASS** — transcript byte-identical
  to 12 Nov except P1:5; 27 ticks; heap bump 33808; net 4/3/1.
  New `test_kernel_unified_idle.py` **10/10 PASS** — transcript
  `KERN / > z / Z4 / > w / K10W0 / > q / BYE`: sleep demo starts at
  tick 4, wakes at tick 10 (6 ticks ≥ the 5-tick sleep — with the
  old immediate resume the wake tick would have been ~4); halts;
  final states [running, idle, done, free]; idle pid 1; sleeper
  pid 2; final ticks 11. `test_kernel_idle.py` **8/8 PASS**
  unchanged. Full standalone suite, fresh checkpoint: **118 pass /
  0 fail / 9 skip of 127 files, 509 checks, 42.3 s** (12 Nov was
  117 pass / 499 checks — +1 file, +10 checks, both the new test).
  Logs: `~/workspace/blackmoon-iso/os/idle-unified/`.
- Runner-ups (not this slice): adopt the lifetime allocator into the
  unified kernel; Notes as third desktop app (needs iverilog/SOC2);
  kernel_pix/kernel_full 640-wide re-runs.

## Slice 1: THE IDLE TASK — DONE + PUSHED 12 Nov ~13:00 IST
- Files: examples/os/kernel_idle.fg (md5 262de581…), tests/test_kernel_idle.py (md5 87dcdf60…). Nothing existing modified.
- Design: idle task is a real spawned task in slot 1 (new state 5), children in slots 2–3; one new scratch cell (idle pid at 0x8050); all three no-ready paths (sleep/yield/exit) switch to idle when a sleeper exists; interrupt path restores idle state to 5. One bug caught on re-read before running (yield path would have clobbered idle mepc via csr_write — fixed with early return).
- Verified by coordinator from own runs + logs (Python big32 model only; no SOC2 — iverilog absent): exact transcript **KERNA8DONE**, halted, **10,250 steps**, identical across two independent rebuilds; wake tick **8** ≥ sleep 5; final tick 9; final states [running, idle, done, free]; test **8/8 PASS twice**; sibling test_kernel_drivers.py 0 failures. Built with QASIDA_COMPILER=python (build --target big32 dispatches to Python by design; hosted defers non-native targets). No NEEDS items.
- Push: first attempt killed at 817 blobs by a service restart (remote stayed 90d2f8f9 — nothing landed); relaunched, **PUSH VERIFIED 90d2f8f9 → 9fa4926d34be14d3426fef9221124364b0d58898**; read-back matched both new files by blob SHA (kernel_idle.fg 72d9fef7…, test_kernel_idle.py 3857ee42…); remote main confirmed at 9fa4926d. No tag, no release.
- Next slice (implementer recommendation): adopt the idle task into kernel_unified.fg (it still carries the old limitation in its docstring) — same three no-ready paths, re-run test_kernel_unified.py plus a sleep-with-nobody-ready case. DONE 13 Nov 2026, recorded as Slice 2 above. Runner-up: lifetime allocator v2 into the unified kernel.
