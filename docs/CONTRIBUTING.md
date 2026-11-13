# Contributing

> This guide was partly AI-generated.
>
> SI2530 / FSI3080 HT26 — Hybrid Monte Carlo for a Lennard-Jones Fluid
> KTH Computational Physics | Eric Enderborg

## Start here

Complete [Getting Started](GETTING_STARTED.md) first for installation and development-environment setup.

This guide describes the current local merge-gate script and the supplied GitHub Actions workflow. Keep both updated when checks change.

## Run the local merge gate

From the repository root, in Bash (Git Bash on Windows):

```bash
bash tools/scripts/merge_gate.sh
```

This is the normal pre-push command. It automatically builds the extension, invokes the stub generator, runs tests, and typechecks. You do not need to run several scripts manually.

### What it runs

1. Set up or reuse `.venv-gate` and check for Python 3.12.
2. Install missing Python check/build dependencies and ensure Rust lint components are available.
3. Run Python formatting and lint checks.
4. Run Rust formatting and Clippy checks.
5. Build/install the extension into the gate environment.
6. Generate `lj_hmc/_core.pyi` using `tools/gen_stubs.py`.
7. Run Rust and Python tests.
8. Verify generated stubs against Git.
9. Run Pyright after stub generation.
10. Print each job result and return failure if a job failed.

Jobs continue independently after a failure; each job stops at its first failing command. For example, failing Python tests prevent stub verification in that job, but the later typecheck still runs.

### Options

| Option | Behavior |
|---|---|
| No options | Full gate; keep `.venv-gate` afterwards. |
| `--fast` | Python/Rust lint plus Pyright; skip extension build, stub generation, and tests. |
| `--fix` | Apply Ruff fixes and Python/Rust formatting, then run the remaining checks. |
| `--use-current` | Use the already-activated virtualenv instead of `.venv-gate`; may install tools and replace its extension build. |
| `--clean` | Delete the activated gate environment after the run; does not delete your environment with `--use-current`. |
| `--help` | Display usage. |

```bash
bash tools/scripts/merge_gate.sh --fast
bash tools/scripts/merge_gate.sh --fix
bash tools/scripts/merge_gate.sh --fix --fast
```

Fast mode requires an existing stub and is not a full gate pass. `--clean` removes the environment after running; it does not start by clearing an existing environment.

## Development environment versus gate environment

| Directory | Purpose |
|---|---|
| `.venv/` | Interactive work, simulations, and editor integration. |
| `.venv-gate/` | Reusable environment managed by the local gate. |

Keep both in `.gitignore`:

```gitignore
.venv/
.venv-gate/
```

The first gate run installs dependencies. Subsequent runs reuse installed versions and install anything missing. It is not a fresh CI environment on every run.

To upgrade gate dependencies on Windows:

```bash
.venv-gate/Scripts/python.exe -m pip install --upgrade \
    ruff pyright maturin pytest numpy h5py matplotlib
```

On Linux/macOS:

```bash
.venv-gate/bin/python -m pip install --upgrade \
    ruff pyright maturin pytest numpy h5py matplotlib
```

## Daily workflow

| Change | Action |
|---|---|
| Python implementation | Run relevant tests; usually no extension rebuild. |
| Rust implementation | Rebuild in your development environment; run the full gate before pushing. |
| Rust API | Run the full gate; review and commit regenerated stubs. |
| Packaging/build configuration | Rebuild and run the full gate. |
| Formatting/lint issue | Use `--fix`, then review edits. |
| Any change before push | Run the full gate and inspect its summary. |

See Getting Started for debug/release build commands. The gate installs a debug extension into its selected environment.

## Type stubs

`lj_hmc/_core.pyi` describes the compiled Rust extension to static tools. Keep it committed: the independent CI typecheck job does not build the extension.

The full gate invokes the generator automatically after building. Generated stubs must be reviewed, not edited manually.

### When the stub changes

```bash
git status --short
git diff -- lj_hmc/_core.pyi
```

For a newly generated, untracked file, open it directly; `git diff` does not show its contents.

After review:

```bash
git add lj_hmc/_core.pyi
# Include related source changes in the same commit as appropriate.
git commit -m "Update extension type stubs"
bash tools/scripts/merge_gate.sh
```

The local gate compares tracked stubs against `HEAD`, so staging without committing does not clear the check. It also detects untracked `.pyi` files and verifies that the extension stub is tracked.

If generation introduces formatting differences, fix the generator rather than repeatedly formatting its output by hand. Its output should be deterministic and end in exactly one newline. The current generator only handles exposed functions; review its output and limitations when extending the Rust API. Passing stub freshness does not prove the signatures have complete or correct type annotations.

## Adding Rust functions

1. Implement the function in `engine/src/lib.rs` with `#[pyfunction]`.
2. Register it in the PyO3 `_core` module.
3. Add or update tests.
4. Run the full gate.
5. Review the generated stub and commit it with the source changes.
6. Rerun the full gate before pushing.

Keep the extension name consistent across:

- `[lib] name = "_core"` in `engine/Cargo.toml`.
- The PyO3 module export named `_core`.
- `module-name = "lj_hmc._core"` in `pyproject.toml`.

### Relevant layout

```text
lj-fluid-hmc/
├── pyproject.toml
├── engine/
│   ├── Cargo.toml
│   └── src/lib.rs
├── lj_hmc/
│   ├── __init__.py
│   └── _core.pyi
└── tools/
    ├── gen_stubs.py
    └── scripts/merge_gate.sh
```

```toml
[tool.maturin]
manifest-path = "engine/Cargo.toml"
module-name = "lj_hmc._core"
python-source = "."
```

`python-source` is the directory containing the Python package, not the Python interpreter or virtualenv.

## Tool configuration and exclusions

Keep shared configuration in `pyproject.toml` (or the tool's existing dedicated configuration), not only in the local shell script. Local checks and CI should use the same rules.

- Preserve existing Ruff exclusions when adding new ones.
- Use the exact spelling and case of paths; CI runs on Linux.
- Keep generated/vendor stubs separate from code you maintain.
- Do not suppress errors in application code merely to make the gate pass.
- Keep the generated extension stub available to Pyright even if it is excluded from linting.

## GitHub Actions

The supplied workflow is `.github/workflows/Merge_gate.yaml`. Use the actual filename and case in the repository.

It runs on pull requests and pushes to `main`.

| Job | Checks |
|---|---|
| `lint-python` | Ruff format check and lint. |
| `typecheck` | Pyright. |
| `lint-rust` | Cargo formatting and Clippy with warnings denied. |
| `build-test` | maturin build, Rust tests, Python tests, stub generation/freshness. |
| `gate` | Requires all four upstream jobs to succeed. |

### Differences from local checks

- CI runs on Ubuntu; your local gate uses your OS and toolchain.
- CI jobs have separate environments; local jobs share `.venv-gate`.
- CI installs dependencies afresh; the local gate reuses installed versions.
- CI checks the pushed commit; local checks also see uncommitted changes.
- The local script generates stubs before Pyright; CI typechecking relies on committed stubs.
- The supplied CI stub check uses `git diff --exit-code`, which does not detect untracked files. The local script additionally checks those and compares tracked stubs to `HEAD`.

A local pass is not a guarantee of a CI pass. Keep the workflow and local script aligned deliberately.

## Before pushing

- [ ] Add or update tests for changed behavior.
- [ ] Run `bash tools/scripts/merge_gate.sh` without `--fast`.
- [ ] Review formatting fixes and generated stub changes.
- [ ] Commit the relevant changes and any generated stubs.
- [ ] Rerun the gate if it failed because stubs were not committed.
- [ ] Check `git status --short` for unexpected files.
- [ ] Ensure `.venv/`, `.venv-gate/`, and compiled build artifacts are not committed.
- [ ] Inspect CI after pushing.

## Troubleshooting

| Problem | Action |
|---|---|
| Gate reports Python version mismatch | Install Python 3.12 and recreate the gate environment with that version. |
| Gate activation fails on Windows | Check for `.venv-gate/Scripts/activate` and use the updated script. |
| `_core` is unknown to Pyright | Run the full gate and verify `lj_hmc/_core.pyi` exists and is committed. |
| Stub generation writes under `tools/lj_hmc/` | Correct the generator to resolve the repository root, one level above `tools/`. |
| Generated file always fails formatting | Fix the generator's output; do not rely on manual edits. |
| Stub check fails after `git add` | The local check compares to `HEAD`; review and commit, then rerun. |
| Tests pass but stub generation fails | The whole job still fails; inspect the generator traceback. |
| `cargo test` says zero tests | No Rust tests were executed; this is not evidence of Rust unit-test coverage. |
| Tests unexpectedly disappear | Check collected test names and discovery configuration, not just the pass count. |
| Local pass, CI failure | Compare dependencies, platform, committed files, and tool configuration. |

For installation and compiler setup problems, see [Getting Started](GETTING_STARTED.md).
