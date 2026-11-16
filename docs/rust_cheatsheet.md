# Rust & PyO3 Cheat-Sheet

Quick-reference commands for developing, testing, building, and maintaining the Rust physics kernel (`engine/`) from the repository root.

---

## 1. Everyday Development Loop

When you edit Rust code, the standard workflow is:

```bash
# 1. Quick syntax & type check (fastest feedback while coding):
cargo check

# 2. Run Rust unit tests:
cargo test

# 3. Build & link into your active Python .venv (debug mode):
maturin develop

# 4. Regenerate Python type stubs (if you changed or added Rust functions):
python tools/gen_stubs.py

# 5. Run Python integration tests:
pytest
```

---

## 2. Testing (`cargo test`)

Run these directly from the repository root:

| Task | Command | Notes |
| :--- | :--- | :--- |
| **Run all Rust tests** | `cargo test` | Runs all `#[test]` functions across `src/*.rs`. |
| **Show print outputs** | `cargo test -- --nocapture` | Shows `println!` debugging statements inside passing tests. |
| **Run specific test** | `cargo test test_minimum_image` | Runs any test whose name matches the substring. |
| **Run specific module** | `cargo test pbc::` | Runs only tests inside `src/pbc.rs`. |
| **Run Python tests** | `pytest` | Runs all pytest tests in `tests/unit/`. |

---

## 3. Building the Python Extension (`maturin develop`)

Maturin compiles your Rust code into a C-extension `.pyd` and registers it directly inside your active `.venv`.

| Task | Command | When to use |
| :--- | :--- | :--- |
| **Debug build (fast)** | `maturin develop` | Everyday coding, testing, and debugging. |
| **Release build (optimized)** | `maturin develop --release` | **Production runs, benchmarking, and timing studies.** Enables `-O3`, LTO, and max compiler optimizations. |

> **Remember:** If you change a function signature or add a new `#[pyfunction]` in Rust, always run:
> ```bash
> python tools/gen_stubs.py
> ```
> This updates `lj_hmc/_core.pyi` so VS Code and Pyright provide autocompletion and type checking for the new Rust functions.

---

## 4. Linting, Formatting & Quality Checks

Run these before opening a PR or committing code:

| Task | Command | Description |
| :--- | :--- | :--- |
| **Auto-format Rust** | `cargo fmt` | Automatically formats all `.rs` files according to standard style. |
| **Check Rust format** | `cargo fmt --check` | Verifies formatting without modifying files (used in CI). |
| **Rust Linter (Clippy)** | `cargo clippy` | Catches non-idiomatic code, performance bottlenecks, and potential bugs. |
| **Strict Clippy (CI mode)** | `cargo clippy -- -D warnings` | Treats any Clippy warning as an error. |
| **Python Linter & Formatter** | `ruff check .` / `ruff format .` | Runs Ruff on Python files. |

---

## 5. Full Merge-Gate Check

To run all Rust and Python checks, tests, formatting, and typechecking at once (identical to GitHub Actions CI):

```bash
# Run complete CI test suite locally (in Git Bash):
bash tools/scripts/merge_gate.sh

# Automatically fix format and lint issues:
bash tools/scripts/merge_gate.sh --fix
```

---

## 6. Troubleshooting & Common Gotchas

### `STATUS_DLL_NOT_FOUND (exit code 0xc0000135)`
* **Cause:** Windows cannot find `python312.dll` when launching the `cargo test` executable.
* **Fix:** Make sure `.venv` is activated (it sets the DLL path), or manually run:
  ```bash
  export PATH="/c/Users/erice/AppData/Local/Programs/Python/Python312:$PATH"
  ```

### Build cache is bloated or acting strange
To wipe all compiled Rust artifacts and start completely fresh:
```bash
cargo clean
maturin develop
```

### Python imports old/stale Rust code
* If you edit `.rs` files, Python does **not** pick up the changes until you re-run:
  ```bash
  maturin develop
  ```
