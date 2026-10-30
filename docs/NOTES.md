# Monte Carlo Method

## Monte Carlo Method (Equilibrium Statistical Physics - Plischke, Bergersen)
### Short Description:
In monte carlo methods (MC) one does not attempt to simulate the dynamics of the system. The idea rather, is to generate states *i, j, ...* by a stochastic process such that the probability *$\pi (i) $* of state *i* is that given by the appropriate distribution (canonical, grand canonical, etc). 

In a ``production run´´ of a simulation **N** states are generated and the desired quantity $x_i$ (energy, magnetization, pressure, etc) is calculated for each state. If the probabilities are correct: 

$$
\langle x \rangle = \lim_{N \to \infty} \frac{1}{N}\sum_i x_i
$$.

Most often one simulates the canonical ensemble (thermal average):

$$
\pi(i) = \frac{1}{Z}e^{-\beta E(i)} \quad Z = \sum_i e^{-\beta E(i)}
$$

This leads to two questions:

1) How does the computer generate states?
Answer:  
2) How can I make sure that the probabilities are right?




## Monte Carlo Method (Understanding Molecular Simulation - Frenkel, Smit)

$\mathcal{H} = \mathcal{K} + \mathcal{V}$

Partition function: $Z = \int{ d\mathbf{r}^N \exp(-\beta \mathcal{V}(\mathbf{r}v^N))}$

$\mathcal{N}(\mathbf{r}^N) = \exp(-\beta \mathcal{V}(\mathbf{r}v^N)) / Z$ is the probability density of finding the system in a configuration around $\mathbf{r}^N$

Suppose we are randomly able to generate points in configuration space according to $\mathcal{N}$. This means that, on average, the number of points $n_i$ generated per unit volume around a point $\mathbf{r}^N$ is equal to $L\mathcal{N}(\mathbf{r})^N$ where $L$ is the total number of points that we have generated:

"in the Metropolis scheme, a random walk is constructed through that region of space where the integrand is nonnegligible"
In this random walk a trial move is rejected if it takes you out of the water (Measuriring depth of Nile example) and accepted otherwise.

## Metropolis Monte Carlo



---

# Rust Integration (PyO3 + Maturin)

### Everyday Commands
```bash
# Rebuild into active .venv after editing Rust code (fast, debug mode):
maturin develop

# Rebuild with full compiler optimizations (-O3, use for benchmarking/production):
maturin develop --release

# Run tests:
pytest
```

### Exposing Rust functions to Python
Edit `engine/src/lib.rs`:

1. Annotate the function with `#[pyfunction]`:
```rust
#[pyfunction]
#[pyo3(signature = (r, epsilon, sigma))]
pub fn lennard_jones(r: Vec<f64>, epsilon: f64, sigma: f64) -> PyResult<f64> {
    // calculation here...
    Ok(result)
}
```

2. Register it in the module at the bottom:
```rust
#[pymodule]
fn engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(lennard_jones, m)?)?;
    Ok(())
}
```

3. Call `maturin develop`, then in Python:
```python
from engine import lennard_jones
```

# Lennard-Jones Fluid
A Lennard-Jones fluid refers to the macroscopic N-particle system whose potential energy is modeled as the sum of these pairwise interactions:
$$
U(\mathbf{r}^N) = \sum _{i<j} ^N u^{Lj}(r_{ij})
$$
where r is the displacement vector (dx, dy, dz).
Lennard-Jones potential:
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

So when calculating the total internal potential  energy of a Lennard-Jones fluid we use:
$$
U(\mathbf{r}^N) = \sum_{i=1}^{N-1} \sum_{j=i+1}^N u(\mathbf{r_{ij}})
$$
to avoid double counting.

## Reduced units

Dimensionless expressions for all system quantities used in the simulation, as summarized in the table below.

| Quantity | Reduced unit | Relation to SI |
|----------|:------------:|:---------------|
| Length | $r^*$ | $r\sigma^{-1}$ |
| Energy | $E^*$ | $E\epsilon^{-1}$ |
| Temperature | $T^*$ | $k_B T\epsilon^{-1}$ |
| Time | $t^*$ | $t\sigma^{-1}\sqrt{\epsilon/M}$ |
| Mass | $m^*$ | $mM^{-1}$ |
| Force | $F^*$ | $F\sigma\epsilon^{-1}$ |
| Density | $\rho^*$ | $N\sigma^3V^{-1}$ |
| Pressure | $p^*$ | $p\sigma^3\epsilon^{-1}$ |
| Velocity | $v^*$ | $v\sqrt{M/\epsilon}$ |

*Reduced Lennard-Jones units used in the simulations.*

# Velocity Verlet Integrator
Page 75 of Frenkel,Smit

$$


$$

# Algorithm

## In simple terms
### Phase 1: Init
1) Position *(Frenkel & Smit: Chapter 4, Section 4.2.1, Page 65, Algorithm 4)*
2) Forces and Energy *(Frenkel & Smit: Chapter 4, Section 4.2, Page 65, Algorithm 3 & 5)*

### Phase 2: Traj loop
3) Draw random *Momenta* for each particle from Maxwell-Boltzmann distribution *(Frenkel & Smit: Chapter 14, Section 14.2, Page 398; Chapter 6, Section 6.1, Page 143–144, Algorithm 15)*
4) Hamiltonian of state: $H_{\text{old}} = U(\mathbf{r}) + K(\mathbf{p})$ *(Frenkel & Smit: Chapter 3, Section 3.1, Eq. 3.1.1, Page 31; Chapter 14, Section 14.2, Page 398)*
    ### Phase 2.5: Molecular Dynamics Trajectory (Loop for $l = 1$ to $L$ steps)
    5) Update "half-kick" momenta for all particles: $\mathbf{p} \leftarrow \mathbf{p} + \frac{\mathbf{f}}{2}\Delta t$ *(Frenkel & Smit: Chapter 6, Section 6.1, Page 143–144, Algorithm 14/15; Appendix E.2, Page 537–538)*
    6) Use step 5 momenta to introduce drift to position: $\mathbf{r} \leftarrow \mathbf{r} + \frac{\mathbf{p}}{m}\Delta t$ *(Frenkel & Smit: Chapter 6, Section 6.1, Page 143–144, Algorithm 15; Appendix E.2, Page 537–538)*
    7) Use derivative of Lennard-Jones potential on new drifted positions for all particles to get new forces *(Frenkel & Smit: Chapter 4, Section 4.2, Page 65, Algorithm 5)*
    8) Add rest of "kick" momenta: $\mathbf{p} \leftarrow \mathbf{p} + \frac{\mathbf{f}_{\text{new}}}{2}\Delta t$ *(Frenkel & Smit: Chapter 6, Section 6.1, Page 143–144, Algorithm 15; Appendix E.2, Page 537–538)*

### Phase 3: Metropolis Acceptance
9) Calculate new global Hamiltonian $H_{\text{new}} = U(\mathbf{r}_{\text{new}}) + K(\mathbf{p}_{\text{new}})$ *(Frenkel & Smit: Chapter 14, Section 14.2, Page 398)*
10) Compute $\Delta H = H_{\text{new}} - H_{\text{old}}$ *(Frenkel & Smit: Chapter 14, Section 14.2, Page 398)*
11) Draw uniformly distributed number $\alpha \in [0, 1)$ *(Frenkel & Smit: Chapter 3, Section 3.2.1, Page 33, Algorithm 2)*
12) Metropolis acceptance criterion: keep move if $\alpha < \exp(-\beta \Delta H)$ (always accept if $\Delta H \le 0$; accept probabilistically if $\Delta H > 0$), else restore old position and momenta *(Frenkel & Smit: Chapter 3, Section 3.1.2, Page 27; Section 3.2.1, Page 32, Eq. 3.2.1; Chapter 14, Section 14.2, Page 398)*