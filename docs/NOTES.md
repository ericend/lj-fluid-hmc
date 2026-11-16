# Theoretical Notes & Algorithm Reference

Personal study notes and textbook references for the Lennard-Jones simulation project.

---

## 1. Statistical Mechanics & Monte Carlo Fundamentals

### Canonical Ensemble ($NVT$)
*(Reference: Plischke & Bergersen, Equilibrium Statistical Physics)*

In Monte Carlo (MC) methods, one does not simulate real-time physical dynamics. Instead, states $i, j, \dots$ are generated stochastically such that the probability $\pi(i)$ of observing configuration $i$ corresponds to the canonical distribution:

$$
\pi(i) = \frac{1}{Z} e^{-\beta E(i)}, \quad Z = \sum_i e^{-\beta E(i)}
$$

where $\beta = \frac{1}{k_B T}$. In a production simulation of $M$ sampled states, the thermal expectation value of any observable $A$ converges to:

$$
\langle A \rangle = \lim_{M \to \infty} \frac{1}{M} \sum_{i=1}^M A(i)
$$

### Configuration Space Sampling
*(Reference: Frenkel & Smit, Understanding Molecular Simulation, Ch. 3)*

For classical particles with Hamiltonian $\mathcal{H} = \mathcal{K}(\mathbf{p}) + \mathcal{U}(\mathbf{r})$, the kinetic and potential contributions factor in the partition function:

$$
Z \propto \left( \int d\mathbf{p}^N e^{-\beta \mathcal{K}(\mathbf{p})} \right) \left( \int d\mathbf{r}^N e^{-\beta \mathcal{U}(\mathbf{r}^N)} \right)
$$

The configurational probability density is:

$$
\mathcal{N}(\mathbf{r}^N) = \frac{e^{-\beta \mathcal{U}(\mathbf{r}^N)}}{\int d\mathbf{r}^N e^{-\beta \mathcal{U}(\mathbf{r}^N)}}
$$

In the Metropolis scheme, a random walk is constructed through configuration space where trial moves are accepted or rejected to satisfy **detailed balance**:

$$
\pi(o) \alpha(o \to n) \text{acc}(o \to n) = \pi(n) \alpha(n \to o) \text{acc}(n \to o)
$$

For a symmetric trial move distribution $\alpha(o \to n) = \alpha(n \to o)$, this simplifies to the Metropolis criterion:

$$
\text{acc}(o \to n) = \min\left(1, e^{-\beta [U(n) - U(o)]}\right)
$$

---

## 2. Symplectic Dynamics: Velocity Verlet Integrator
*(Reference: Frenkel & Smit, Ch. 4, Sec. 4.3, p. 75)*

The Velocity Verlet algorithm is a time-reversible, symplectic numerical integrator that integrates Newton's equations of motion:

1. **Half-kick in momentum / velocity:**
   $$
   \mathbf{p}\left(t + \frac{\Delta t}{2}\right) = \mathbf{p}(t) + \frac{\Delta t}{2} \mathbf{f}(\mathbf{r}(t))
   $$

2. **Full-step coordinate drift:**
   $$
   \mathbf{r}(t + \Delta t) = \mathbf{r}(t) + \Delta t \frac{\mathbf{p}\left(t + \frac{\Delta t}{2}\right)}{m}
   $$

3. **Compute updated forces:**
   $$
   \mathbf{f}(\mathbf{r}(t + \Delta t)) = -\nabla U(\mathbf{r}(t + \Delta t))
   $$

4. **Second half-kick in momentum:**
   $$
   \mathbf{p}(t + \Delta t) = \mathbf{p}\left(t + \frac{\Delta t}{2}\right) + \frac{\Delta t}{2} \mathbf{f}(\mathbf{r}(t + \Delta t))
   $$

---

## 3. Hybrid Monte Carlo (HMC) Algorithm Step-by-Step

*(Reference: Frenkel & Smit, Ch. 14, Sec. 14.2, pp. 396–400; Duane et al., 1987)*

HMC combines molecular dynamics with Metropolis acceptance to allow large, collective coordinate updates while preserving the exact canonical distribution:

### Phase 1: Initialization
1. Initialize particle positions $\mathbf{r}$ on an FCC lattice at target density *(FS02 Ch. 4, Alg. 4)*.
2. Evaluate initial forces $\mathbf{f}$ and potential energy $U(\mathbf{r})$ *(FS02 Ch. 4, Alg. 3 & 5)*.

### Phase 2: Trajectory Generation
3. **Momentum Refresh:** Draw fresh random momenta $\mathbf{p}_i$ for each particle independently from the Maxwell-Boltzmann distribution:
   $$
   p_{i,\alpha} \sim \mathcal{N}(0, m k_B T)
   $$
   *(FS02 Ch. 6, Alg. 15; Ch. 14, Sec. 14.2)*.
4. **Initial Hamiltonian:** Calculate total energy of the state:
   $$
   H_{\text{old}} = U(\mathbf{r}) + \sum_{i=1}^N \frac{\mathbf{p}_i^2}{2m}
   $$
5. **Molecular Dynamics Trajectory:** Propagate phase space $(\mathbf{r}, \mathbf{p})$ forward for $L$ Velocity Verlet steps of size $\Delta t$:
   - $\mathbf{p} \leftarrow \mathbf{p} + \frac{1}{2}\mathbf{f}\Delta t$
   - $\mathbf{r} \leftarrow \mathbf{r} + \frac{\mathbf{p}}{m}\Delta t$
   - Fold $\mathbf{r}$ with periodic boundary conditions (minimum image convention)
   - Evaluate new forces: $\mathbf{f}_{\text{new}} \leftarrow -\nabla U(\mathbf{r})$
   - $\mathbf{p} \leftarrow \mathbf{p} + \frac{1}{2}\mathbf{f}_{\text{new}}\Delta t$

### Phase 3: Metropolis Acceptance
6. **Proposed Hamiltonian:** Calculate:
   $$
   H_{\text{new}} = U(\mathbf{r}_{\text{new}}) + \sum_{i=1}^N \frac{\mathbf{p}_{\text{new}}^2}{2m}
   $$
7. **Hamiltonian Difference:**
   $$
   \Delta H = H_{\text{new}} - H_{\text{old}}
   $$
8. **Acceptance Step:** Draw uniform random number $\xi \sim \mathcal{U}[0, 1)$:
   - If $\xi < \min(1, e^{-\beta \Delta H})$: accept new positions $\mathbf{r}_{\text{new}}$.
   - Otherwise: reject trial trajectory and retain old positions $\mathbf{r}_{\text{old}}$.
