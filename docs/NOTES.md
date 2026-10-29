### Monte Carlo Method

## Monte Carlo Method (Equilibrium Statistical Physics - Plischke, Bergersen)
# Short Description:
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

### Metropolis Monte Carlo



---

## Rust Integration (PyO3 + Maturin)

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
