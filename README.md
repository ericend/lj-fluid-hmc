# Hybrid Monte Carlo simulation for a Lennard-Jones fluid

### SI2530 - FSI3080 HT26 Computational Physics | KTH | Eric Enderborg | November 2026

### Short Project Description:
Implements HMC (Hybrid/Hamiltonian Monte Carlo) updates in a Lennard-Jones particle simulation and compares efficiency to Metropolis Monte Carlo moves.

## Tech Stack:

### Rust / C++

### Python

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

### Leapfrog Integrator

### NUTS (No U-turn Sampler)

### 

## Implementation:

### Software Design



## Analysis:

### Verification against previous simulation
(Argon lab)

## Results

### Recreation of results

### Algorithm Benchmarks

