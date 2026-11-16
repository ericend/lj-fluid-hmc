# Hybrid Monte Carlo simulation for a Lennard-Jones fluid
**SI2530 / FSI3080 HT26 Computational Physics** | KTH | Eric Enderborg | November 2026

> This README was partly AI-generated.

## Project Description:


This project aims to first implement a standard Metropolis Monte Carlo program to simulate a Lennard-Jones fluid (argon) in the canonical ($NVT$) ensemble, and subsequently expand upon it by implementing Hybrid (Hamiltonian) Monte Carlo (HMC) updates to compare sampling efficiency and autocorrelation times.

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


## Tech Stack

### Rust kernel
The physics kernel is written in Rust and exposed to Python via PyO3.

### Python
Python serves as the simulation frontend, handling experiment configuration, analysis, and visualization.

## Model:

### Lennard-Jones fluid
A Lennard-Jones fluid refers to the macroscopic N-particle system whose potential energy is modeled as the sum of these pairwise interactions:
$$
U(\mathbf{r}^N) = \sum _{i<j} ^N u^{Lj}(r_{ij})
$$
where $\mathbf{r}$ is the displacement vector (dx, dy, dz).

The Lennard-Jones potential is given by:
$$
u^{Lj}(r)=4 \epsilon \left[  \left( \frac{\sigma}{r} \right)^{12} - \left( \frac{\sigma}{r} \right) ^6 \right]
$$.
* Short Range Repulsion: $\propto r^{-12}$ models the electrostatic repulsion between overlapping electron clouds (Pauli principle) when two atoms get very close.
* Long Range Attraction: $\propto r^{-6}$ Models van der Waals interaction caused by dipole-induced fluctuations.
* Energy Scale: $\epsilon$ represents the potential well depth (strength of the interaction)
* Lenght Scale: $\sigma$ Represents the effective core size of the atom where $u^{Lj}(\sigma) = 0$
* It is effectively the standard model of liquid state physics.
* It captures real phase transitions.
* It succeeds particularly well for noble gasses such as argon.


### Velocity Verlet Integrator

### Markov Chain Monte Carlo (MCMC)

### Metropolis Monte Carlo

### Hybrid Monte Carlo (HMC)

### NUTS (No U-turn Sampler) (maybe?)

## Development

See [Getting Started](docs/GETTING_STARTED.md) for full setup instructions. In short:

- **CI** — every PR is gated on Python lint, type-checking (Pyright), Rust lint (Clippy + fmt), and the full test suite.

## Implementation:

### Software Design


The codebase follows a **two-layer hybrid architecture** that decouples low-level numerical integration from high-level experiment orchestration:

1. **Physics Kernel (`rust/`):** Compiled as a native Python extension using **PyO3** and **Maturin**. It owns the simulation state (particle positions, forces, and simulation box parameters) and executes the tight inner loops—pairwise Lennard-Jones force/energy evaluations, minimum-image periodic boundary conditions, Velocity Verlet integration, and Metropolis/HMC acceptance steps—without Python interpreter overhead.
2. **Orchestration & Analysis Layer (`python/`):** Manages simulation initialization, parameter sweeps, observable logging (potential/kinetic energy, virial pressure, acceptance ratios), integrated autocorrelation time ($\tau_{\text{int}}$) estimation, and plotting.

#### Key Design Choices
* **Reduced Lennard-Jones Units:** Internal kernel calculations operate in dimensionless reduced units.
* **Reproducible PRNG:** Uses a seedable, deterministic random number generator (`rand` crate) inside the Rust kernel so Monte Carlo trajectories and benchmark runs are strictly reproducible.

## Analysis:

### Verification against previous simulation
(Argon lab)

## Results

### Recreation of results

### Algorithm Benchmarks

