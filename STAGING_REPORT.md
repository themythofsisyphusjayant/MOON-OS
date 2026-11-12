# MOON-OS — staging report

Staged 12 Nov 2026 from RED-MOON- (`~/workspace/forge-v2`, remote main `9fa4926d`)
into `~/workspace/os-repo-staging/`. Target repo: `themythofsisyphusjayant/MOON-OS`
(public, main). Nothing was deleted or modified under `~/workspace/forge-v2`.

## Correction to the brief

The brief said "170 .fg files". The source tree holds **169 .fg files + README.md
= 170 entries** in `examples/os/`. Three of the 169 were stale generated
rebase artifacts (`kernel_full_soc2.fg`, `kernel_netdev_soc2.fg`,
`kernel_unified_soc2.fg`); see "Removed" below. Staged `.fg` count: **166**.

## File list (299 files, 794,788 bytes)

| Path | Count / size |
| --- | --- |
| `README.md` (new, MOON-OS) | 5,607 bytes, md5 `5aecd3de095121d6fdc93093b7483a91` |
| `.gitignore` (new) | `__pycache__/`, `*.pyc`, `*.vvp`, `examples/os/*_soc2.fg`, `.venv/` |
| `examples/os/` | 166 `.fg` + `README.md` (JalOS readme, copied as-is) |
| `tests/` | 126 `test_kernel_*.py` (all adapted, see below) |
| `tools/model.py` | 13,505 bytes + provenance header (vendored, see below) |
| `tools/rebase_soc2.py` | 2,237 bytes + provenance header (vendored, see below) |
| `docs/FREESTANDING.md` | 41,689 bytes (copied from RED-MOON- `docs/`, also lives there) |
| `docs/PROGRESS.md` | 5,984 bytes (copied from `blackmoon-iso/os/`, history kept) |

Key files (md5): `examples/os/kernel_idle.fg` `262de581aa8a57ac71adf6d3b4b351dc`
(matches the md5 recorded in `docs/PROGRESS.md`); `examples/os/kernel_unified.fg`
`05dd91eed0a7a9f326080d7dcc1d5067`; `tests/test_kernel_idle.py`
`af3fccc7be0738434f8442c6037dcb2b`.

## Layout decision

Kept the `examples/os/` relative layout (did NOT flatten to `kernel/`): all
126 tests already address kernels as `examples/os/kernel_*.fg`, so keeping it
meant the only test edits were compiler/model resolution. README build
commands match the staged layout exactly.

## Vendored files (not RED-MOON- internals)

- `tools/model.py` — copy of BIG-32 `tools/model.py` (13,505 bytes, stdlib-only,
  exactly one import: `sys`; Jayant's own code). Provenance header added.
  Tests load it from the new repo root, never from `~/workspace/big32`.
- `tools/rebase_soc2.py` — copy of RED-MOON- `tools/rebase_soc2.py`
  (73 lines, stdlib-only). Provenance header added. Needed by
  `test_kernel_full.py` / `test_kernel_netdev.py` to rebase kernels to SOC2 RAM.
  No `forge_lang/` or other compiler internals were bundled.

## Removed (generated artifacts, not source)

`examples/os/kernel_full_soc2.fg`, `kernel_netdev_soc2.fg`,
`kernel_unified_soc2.fg` — rebase outputs that pre-existed in the RED-MOON-
tree. A fresh rebase of current `kernel_full.fg` **differs** from the
checked-in `kernel_full_soc2.fg` (stale artifact), and no test reads any of
the three from the tree (`test_kernel_full.py` regenerates its own;
`test_kernel_netdev.py` writes to a temp dir). They are regenerable on demand
and covered by `.gitignore` (`examples/os/*_soc2.fg`). Source tree untouched.

## Test adaptation (all 126 files touched, script `~/workspace/os-staging-adapt.py`)

Mechanism — every test now resolves the compiler as: `qasida` on `PATH`
(`pip install qasida`) → `$QASIDA_BIN` (a `qasida` binary, or a `forge.py`
checkout; a `.py` path runs via `sys.executable`) → hard error naming both.
No `~/workspace/forge-v2` path is hard-coded anywhere. Post-adaptation grep:
zero `forge.py` / `~/workspace` / `FORGE` references in tests; all 126 pass
`py_compile`.

| Change | Files |
| --- | --- |
| `FORGE = [sys.executable, ROOT/forge.py]` → `_qasida_cmd()` helper block + `QASIDA = _qasida_cmd()`; `FORGE + [` uses rewired to `QASIDA + [` | 118 |
| Inline `[sys.executable, ROOT/forge.py, "build", ...]` → `[*_qasida_cmd(), "build", ...]` (helper inserted after `ROOT = ...`) | 8 (`fb`, `finder`, `full`, `mac`, `mac_int`, `pix`, `term`, `uart16550_soc2`) |
| `MODEL = expanduser("~/workspace/big32/tools/model.py")` → `os.path.join(ROOT, "tools", "model.py")` | 117 |
| `BIG32`/`PROOF` expanduser lines → `$BIG32_DIR` / `$RX_PROOF_DIR` env vars; `.vvp` outputs moved from the rx-proof dir to `TMP`; loud `SKIP SOC2 test` guard at `main()` (prints SKIP, exits 0, no PASS lines) | 9 (SOC tests) |

Unchanged on purpose: `test_kernel_idle.py` keeps `QASIDA_COMPILER="python"`
in the build env (forces the Python compiler path for the big32 target);
`test_kernel_full.py` still writes its regenerated `kernel_full_soc2.fg` into
`examples/os/` (now gitignored); all kernel paths stay `examples/os/...`.

## Tests that could NOT be made standalone (9)

`test_kernel_fb.py`, `test_kernel_finder.py`, `test_kernel_full.py`,
`test_kernel_mac.py`, `test_kernel_mac_int.py`, `test_kernel_netdev.py`,
`test_kernel_pix.py`, `test_kernel_term.py`, `test_kernel_uart16550_soc2.py`.
They need, beyond this repo: a BIG-32 checkout (`src/big32_core_pipe.v`,
`src/big32_soc2.v`), the rx-proof testbenches (`tb_*.v`), and `iverilog`.
Without those they SKIP loudly (verified: `test_kernel_fb.py` prints
`SKIP SOC2 test: ...`, exit 0). The other 117 tests need only the compiler +
this repo. `iverilog` is not installed in this VM.

## Verification (all from the staging dir, real runs)

Gold path — fresh venv `/tmp/moonos-verify/venv`, `pip install qasida`
(installed qasida **2.1.0**, `Requires-Python: >=3.10`), `PATH` set to the
venv bin, run from `~/workspace/os-repo-staging`:

| Command | Result | Exit |
| --- | --- | --- |
| `python tests/test_kernel_idle.py` | **8/8 PASS** — `KERNA8DONE`, wake tick 8, final tick 9 | 0 |
| `python tests/test_kernel_unified.py` | **7/7 PASS** — exact shell-tour transcript, 25 ticks, net 4/3/1 | 0 |
| `python tests/test_kernel_drivers.py` | **6/6 PASS** — `KERNBADONE`, 7 ticks | 0 |

Fallback path — no `qasida` on `PATH`, `QASIDA_BIN=$HOME/workspace/forge-v2/forge.py`:
`tests/test_kernel_idle.py` **8/8 PASS**, exit 0.

Scope: only the two bar tests + drivers were run (per brief — not all 126).
README build commands are exactly the commands run above.

## Push — DONE 12 Nov 2026 ~14:31 IST

- Method: Git Data API tree build (adapted `~/workspace/scripts/push_forge.py`,
  script `~/workspace/push_moonos.py`). 300 files, 300 blobs, 0 retries needed.
- Old remote state (verified by API read before push): commit
  `0adaa818288a3ed02a710e023f8d88546495fd57`, single file `README.md`, blob
  `c13d217f00650bfe86412dbc4117d9350ef4b755`, 9 bytes (`# MOON-OS`).
  **Superseded**: the staged `README.md` (5,607 bytes) replaced it at the same
  path — the carry-over only preserves remote-only files, and `README.md`
  was in the staged tree, so nothing of the old README survives.
- New commit: `2721a87a5fd8a883cd0ebea7227283e92e2d012f`, new tree
  `6089212453b2c16f3f16a7804bf6b39fcd44706b`. Ref `main` updated and verified
  (`verified ref` == new commit). No tag, no release.
- Contents-API read-back at the new commit (script `/tmp/moonos_readback.py`):
  all 12 key files MATCH by blob SHA, remote tree 300 blobs = 300 local files.
  Key blobs: `README.md` `68c685597e0059c70e1809afdfbe128ad63b266a`;
  `examples/os/kernel_idle.fg` `72d9fef71ee32112a5bf46f662ab8d50c1b92264`
  (same blob SHA as the RED-MOON- push recorded in `docs/PROGRESS.md`);
  `examples/os/kernel_unified.fg` `fca82a8a6ff0783e825098cc7f8d47acf1f1f297`;
  `tests/test_kernel_idle.py` `afce73dfd5ddb11e8470b20fd18f9d7d8f8dd4e7`.
