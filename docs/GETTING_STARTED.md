# Getting Started

> **SI2530 / FSI3080 HT26 — Hybrid Monte Carlo for a Lennard-Jones Fluid**
> KTH Computational Physics | Eric Enderborg

This guide walks you through setting up the repository from scratch on a fresh machine.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| **Python** | ≥ 3.12 | [python.org](https://www.python.org/downloads/) |
| **Rust** | stable (≥ 1.80) | [rustup.rs](https://rustup.rs/) — run the installer, restart your terminal |
| **Git** | any | [git-scm.com](https://git-scm.com/) |

> [!IMPORTANT]
> Rust **must** be installed before you can build the `engine` module.
> After running the rustup installer, open a **new** terminal so `cargo` and `rustc` are on your PATH.

---

## 1 — Clone the repository

```powershell
git clone <repo-url>
cd "SI2530 - FSI3080 HT26 Computational Physics/Final"
```

---

## 2 — Create and activate the virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1   # PowerShell
# or: .venv\Scripts\activate.bat   # CMD
```

> [!TIP]
> If PowerShell blocks the activation script, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

## 3 — Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

This installs `numpy`, `pytest`, and `maturin`.

---

## 4 — Build the Rust extension

```powershell
maturin develop
```

This compiles the `engine/` Rust crate and installs it as a native Python module
directly into `.venv`. After this, `import engine` works from anywhere in the project.

### Release build (for benchmarking)

```powershell
maturin develop --release
```

---

## 5 — Run the test suite

```powershell
pytest
```

---

## Project layout

```
Final/
├── core/
│   └── calcs/
│       └── lennard_jones.py       # Pure-Python reference
├── engine/                        # Rust extension
│   ├── Cargo.toml                 # Rust package manifest
│   └── src/
│       └── lib.rs                 # Rust physics kernels
├── tests/
│   └── unit/
│       ├── test_calcs.py          # Tests for the Python reference
│       └── test_engine.py         # Tests for the Rust engine
├── pyproject.toml                 # Maturin build config
├── requirements.txt               # Python dependencies
├── README.md                      # Project description
└── GETTING_STARTED.md             # ← you are here
```

---

## Using the Rust engine in your code

```python
from engine import lennard_jones

# Pairwise potential between two particles
u = lennard_jones(r=[1.5, 0.0, 0.0], epsilon=1.0, sigma=1.0)
```

---

## Adding new Rust functions

1. Write your function in [`engine/src/lib.rs`](engine/src/lib.rs) with the `#[pyfunction]` attribute.
2. Register it in `engine` at the bottom of `lib.rs`.
3. Run `maturin develop`.
4. Import and call it from Python.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `cargo: command not found` | Restart terminal after installing Rust via rustup |
| `maturin: command not found` | Activate the venv first: `.venv\Scripts\Activate.ps1` |
| `ModuleNotFoundError: No module named 'engine'` | Run `maturin develop` |
| PowerShell script blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Build fails with linker error | Install the **MSVC Build Tools**: [aka.ms/buildtools](https://aka.ms/buildtools) — tick "Desktop development with C++" |
