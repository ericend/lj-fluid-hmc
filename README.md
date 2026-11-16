# Hybrid Monte Carlo simulation for a Lennard-Jones fluid
**SI2530 / FSI3080 HT26 Computational Physics** | KTH | Eric Enderborg | November 2026

## Project Description

This project implements a standard Metropolis Monte Carlo program to simulate a Lennard-Jones fluid (argon) in the canonical ($NVT$) ensemble, and expands upon it by implementing Hybrid (Hamiltonian) Monte Carlo (HMC) updates to compare sampling efficiency and autocorrelation times.

<details>
<summary>Original Assignment</summary>

### 1. Write a Monte Carlo program to simulate a Lennard-Jones fluid (e.g., argon) *.
In the computer labs you have used molecular dynamics simulations to simulate argon.
Write a program that implements Monte Carlo simulations instead. Use periodic boundary
conditions and make the simulations at fixed N, V and T. Calculate energy and pressure.
Depending on your ambition you can make use of cutoffs in the interaction and Verlet
neighbor lists, or you can include interactions with all particles. Use the similar parameters,
densities, and temperatures as you used in the MD lab on argon. Check that you get similar
energy and pressure as in the MD-simulations. Don’t forget the kinetic part of energy and
pressure. Experiment with different ways of sampling obeying detailed balance (different
maximum step lengths in the moves and moving one or several particles at the same time)
and monitor how this affects the acceptance ratio. Start from a system equilibrated at
wrong temperature and see how the choice of the moves affect convergence. Is there some
correlation between acceptance ratio and rate of convergence? (See also the following
project ideas for further things to study.)

### 3. Hybrid (Hamiltonian) Monte Carlo simulation for a Lennard-Jones fluid**.
Implement HMC updates in a Lennard-Jones particle simulation and compare its
efficiency with ordinary Metropolis Monte Carlo moves. HMC stands for Hybrid Monte
Carlo or Hamiltonian Monte Carlo and uses an ordinary velocity Verlet integrator to
propose MCMC moves, which are then accepted or rejected based on a Metropolis
criterion. (See e.g., Frenkel-Smit). Make sure you can reproduce the results of the Argon
lab and, in addition, compute the autocorrelation time to quantitatively compare with
Metropolis MC

</details>

---

## Documentation Quick Links

- **[Getting Started](docs/GETTING_STARTED.md)** — Environment setup, building the extension, and verification.
- **[Rust & PyO3 Cheat-Sheet](docs/rust_cheatsheet.md)** — Daily commands for building, testing (`cargo test`), and stub generation.
- **[Theory & Algorithm Notes](docs/NOTES.md)** — Statistical mechanics fundamentals, Metropolis walk, Velocity Verlet, and HMC steps.
- **[Data Storage Reference](docs/h5py_cheatsheet.md)** — Reading and writing simulation data with `h5py`.
- **[Contributing & CI](docs/CONTRIBUTING.md)** — Local merge-gate script, testing standards, and type stubs.

---

## Physical Model

### Lennard-Jones Potential
The macroscopic $N$-particle system interacts via pairwise Lennard-Jones interactions:

$$
U(\mathbf{r}^N) = \sum_{i<j}^N u(r_{ij})
$$

where $r_{ij} = |\mathbf{r}_j - \mathbf{r}_i|$ subject to periodic boundary conditions (minimum image convention). The pair potential is:

$$
u(r) = 4\epsilon \left[ \left(\frac{\sigma}{r}\right)^{12} - \left(\frac{\sigma}{r}\right)^6 \right]
$$

- **Short-range repulsion:** $\propto r^{-12}$ models Pauli exclusion when electron clouds overlap.
- **Long-range attraction:** $\propto r^{-6}$ models attractive London dispersion (induced dipole-dipole fluctuations).
- **Energy scale ($\epsilon$):** Well depth / interaction strength.
- **Length scale ($\sigma$):** Effective atomic collision diameter where $u(\sigma) = 0$.

### Reduced Units
All internal simulation kernels operate in dimensionless reduced Lennard-Jones units:

| Quantity | Reduced Unit | Definition |
| :--- | :---: | :--- |
| **Length** | $r^*$ | $r / \sigma$ |
| **Energy** | $E^*$ | $E / \epsilon$ |
| **Temperature** | $T^*$ | $k_B T / \epsilon$ |
| **Time** | $t^*$ | $t / (\sigma\sqrt{m/\epsilon})$ |
| **Density** | $\rho^*$ | $N \sigma^3 / V$ |
| **Pressure** | $P^*$ | $P \sigma^3 / \epsilon$ |
| **Force** | $F^*$ | $F \sigma / \epsilon$ |

---

## Software Architecture

The codebase follows a **two-layer hybrid architecture** that decouples high-performance numerical routines from experiment orchestration:

1. **Physics Kernel (`engine/`):** Written in Rust and compiled as a native Python extension (`lj_hmc._core`) using **PyO3** and **Maturin**. It executes pairwise distance evaluations under minimum image convention, fast $\mathcal{O}(N)$ local energy changes, and symplectic integration without Python interpreter overhead.
2. **Orchestration Layer (`modules/`):** Manages parameter configuration, FCC lattice initialization, SI $\leftrightarrow$ reduced unit conversions (`SimulationParams`), and Monte Carlo Markov chains.
3. **Analysis Layer (`analysis/`):** Computes thermodynamic observables, block averaging error estimates, autocorrelation times, and publication plots.

### Key Design Choices
- **Dimensionless Core:** All physics computations occur in reduced units; conversion to SI happens at the user boundaries (`modules/system_init/system.py`).
- **Workspace Tooling:** Rust engine managed via root Cargo workspace (`Cargo.toml`) for direct `cargo test` and `cargo clippy` calls.
- **Strict Quality Gate:** All changes pass Python linting/formatting (Ruff), type checking (Pyright), Rust linting (Clippy + rustfmt), and automated tests.
