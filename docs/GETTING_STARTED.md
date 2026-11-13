# Getting Started

> This guide was partly AI-generated.
>
> SI2530 / FSI3080 HT26 — Hybrid Monte Carlo for a Lennard-Jones Fluid
> KTH Computational Physics | Eric Enderborg

## Prerequisites

- Python 3.12. The project declares Python >= 3.12; the local merge gate requires 3.12.
- Rust stable, including Cargo. Open a new terminal after installation.
- Git.
- On Windows: MSVC Build Tools with the **Desktop development with C++** workload.

Git Bash is needed on Windows to run the optional local merge-gate script; ordinary development setup can also use PowerShell.

## 1. Clone the repository

```bash
git clone <repo-url> lj-fluid-hmc
cd lj-fluid-hmc
```

Replace `<repo-url>` with the repository URL. Run subsequent commands from the repository root.

## 2. Create a development environment

### Windows — PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows — Git Bash

```bash
py -3.12 -m venv .venv
source .venv/Scripts/activate
```

### Linux / macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Activate this environment again whenever you open a new terminal for development.

## 3. Install dependencies and build the extension

```bash
python -m pip install -r requirements.txt
python -m maturin develop --manifest-path engine/Cargo.toml
```

These commands assume `requirements.txt` includes `maturin` and the dependencies used by the project. If maturin is missing, install it with `python -m pip install maturin`.

The build installs the project into the active environment in editable mode. The Rust extension is imported as `lj_hmc._core`.

For benchmarking, build the optimized extension instead:

```bash
python -m maturin develop --release --manifest-path engine/Cargo.toml
```

Rebuild after changing Rust code. Ordinary Python source edits generally do not need a rebuild.

## 4. Verify the installation

```bash
python -c "from lj_hmc import _core; print(_core.__file__)"
python -m pytest -rs
```

If pytest is not installed, install the test dependency with `python -m pip install pytest`. Check the test summary for skipped tests as well as failures.

## 5. Initialize a system

The following example constructs the default argon configuration, prints its parameters, and builds an FCC starting lattice. It does not run an HMC trajectory.

```python
from modules.system_init.system import SIInput, SimulationParams

inputs = SIInput(seed=42)
params = SimulationParams(inputs)
positions, box_length_reduced, box_length_angstrom = params.build_fcc_lattice(
    jiggle=0.04
)

params.print_parameters()
print(f"Position array shape: {positions.shape}")
print(f"Reduced box length: {box_length_reduced:.6f}")
```

Save the example in the repository root and run it using the activated development environment. Use package-qualified imports consistently.

## Environments and generated files

- `.venv/` is your development environment.
- `.venv-gate/` is managed separately by the local merge gate.
- Neither environment should be committed.
- Building into `.venv-gate` does not install the extension into `.venv`.
- If you move the project directory, recreate its virtual environments.

## Troubleshooting

| Problem | What to check |
|---|---|
| `cargo: command not found` | Install Rust and open a new terminal. |
| `No module named maturin` | Activate `.venv` and install maturin using `python -m pip`. |
| Cannot import `lj_hmc._core` | Rebuild with maturin in the same environment running your code. |
| PowerShell blocks activation | Use Git Bash, or review the PowerShell execution policy. If appropriate, use `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| Windows linker error | Check that MSVC Build Tools and the C++ desktop workload are installed. |
| maturin cannot find `lj_hmc` | Check the package directory and `python-source` in `pyproject.toml`; it must not point to a virtual environment. |
| VS Code selects the wrong Python | Select the repository's `.venv` interpreter. Check any explicit Pyright venv settings too. |
| Engine tests are skipped | Verify the extension import directly and inspect `pytest -rs` output. |

## Next steps

For development checks, Rust API changes, generated stubs, and the before-push workflow, see [Contributing](CONTRIBUTING.md).
