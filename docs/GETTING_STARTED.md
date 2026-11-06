# Getting Started

> **SI2530 / FSI3080 HT26 — Hybrid Monte Carlo for a Lennard-Jones Fluid**
> KTH Computational Physics | Eric Enderborg

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| **Python** | ≥ 3.12 | [python.org](https://www.python.org/downloads/) |
| **Rust** | stable (≥ 1.80) | [rustup.rs](https://rustup.rs/), then open a **new** terminal |
| **Git** | any | [git-scm.com](https://git-scm.com/) |

On Windows you also need the MSVC Build Tools (see Troubleshooting).

---

## Setup

```powershell
git clone <repo-url> lj-fluid-hmc
cd lj-fluid-hmc

python -m venv .venv
.venv\Scripts\Activate.ps1        # PowerShell
# or: source .venv/Scripts/activate   # Git Bash

python -m pip install -r requirements.txt
maturin develop
pytest -rs
```

> [!TIP]
> If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

> [!NOTE]
> Always use `python -m pip`, so packages go into the venv you are running.
> Venvs store absolute paths. If you move the project folder, recreate `.venv`.

`maturin develop` compiles the Rust crate in `engine/` and installs the project
in editable mode. The compiled module is importable as `lj_hmc._core`.
Use `maturin develop --release` for benchmarking.

---

## Daily workflow

| You changed | Run |
|-------------|-----|
| Python code | nothing (editable install) |
| Rust code, `Cargo.toml`, `pyproject.toml` | `maturin develop` |
| Rust API | `maturin develop`, then `python gen_stubs.py` |
| Anything | `pytest -rs`, `ruff check`, `pyright` |

---

## Usage

Run scripts from the project root:

```python
from lj_hmc import _core
from lj_hmc.lj_fluid_init import AVOGADRO, init_fcc
```

Use one import style everywhere. Mixing `lj_fluid_init` and `lj_hmc.lj_fluid_init`
loads the module twice and breaks `monkeypatch` in tests.

---

## Adding Rust functions

1. Write the function in `engine/src/lib.rs` with `#[pyfunction]`.
2. Register it in `#[pymodule] fn _core`.
3. Run `maturin develop`, then `python gen_stubs.py`.

> [!IMPORTANT]
> `_core` must match in three places: `[lib] name` in `engine/Cargo.toml`,
> the `#[pymodule]` function in `lib.rs`, and `module-name = "lj_hmc._core"`
> in `pyproject.toml`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `cargo: command not found` | Restart the terminal after installing Rust |
| `maturin: command not found` | Activate the venv first |
| `ModuleNotFoundError: lj_hmc._core` | Run `maturin develop`; check `lj_hmc/_core*.pyd` exists |
| `test_engine.py` skipped | Extension not built; run `maturin develop`, then `pytest -rs` |
| Pylance cannot resolve `lj_hmc` | Open the project root, select the `.venv` interpreter, then `Developer: Reload Window`. Pylance reads `[tool.pyright]`, not pytest's `pythonpath` |
| Build error about module name | See the `_core` note above |
| PowerShell script blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Linker error on Windows | Install [MSVC Build Tools](https://aka.ms/buildtools), tick "Desktop development with C++" |
