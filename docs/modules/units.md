# Design of the `units` Module

## 1. Purpose and rules

The simulation core runs entirely in reduced Lennard-Jones units. `units.py` is the only place where SI values are converted, both when setting up a run and when analysing stored data.

- Every scale is defined by one formula, in one place.
- SI values never enter the physics code. HMC, lattice and potential modules read dimensionless values only and never import `units.py`.
- HDF5 files store the user input and the observables in reduced units. SI is computed on demand, so nothing is duplicated.
- Loading is strict: a missing parameter raises an error instead of falling back to current defaults.
- Invalid input fails at construction, before any simulation work.

## 2. Module contents

```
units.py
|-- K_B, N_A         physical constants (Final floats)
|-- Num              TypeVar: float | float64 array
|-- SIInput          user-editable input (SI + settings)
|-- SIUnits          all unit scales in SI
|-- Reduced          dimensionless values for the simulation
|-- Quantity         (scale name, SI label, reduced label)
|-- QUANTITIES       registry: observable name -> Quantity
`-- LJUnits          builds everything, does conversions
```

| Part | Holds |
|---|---|
| `SIInput` | `temperature`, `mass_density`, `sigma`, `epsilon`, `molar_mass`, `n_cells`, `dt`, `n_steps`, `r_cut`, `n_iter`, `n_eq`, `seed` |
| `SIUnits` | Original: `sigma`, `epsilon`, `molar_mass`. Derived: `mass`, `temperature`, `time`, `velocity`, `force`, `pressure`, `number_density`, `mass_density`, `diffusion` |
| `Reduced` | `T`, `rho`, `n_particles`, `l_box`, `dt`, `n_steps`, `r_cut`, `n_iter`, `n_eq`, `seed`, and $\sigma=\epsilon=m=1$ |
| `QUANTITIES` | Observables `U`, `K`, `H`, `T`, `P`, `rho`, `t`, `r`, `v`, `F`, `D`, each mapped to its scale |

### Unit scales (`SIUnits`)

$M = M_\text{mol}/N_A$ is the mass of one atom.

| Quantity | Scale | SI unit |
|---|---|---|
| Length | $\sigma$ | m |
| Energy | $\epsilon$ | J |
| Temperature | $\epsilon/k_B$ | K |
| Mass | $M$ | kg |
| Time | $\tau=\sigma\sqrt{M/\epsilon}$ | s |
| Velocity | $\sqrt{\epsilon/M}$ | m/s |
| Force | $\epsilon/\sigma$ | N |
| Pressure | $\epsilon/\sigma^{3}$ | Pa |
| Number density | $\sigma^{-3}$ | 1/m³ |
| Mass density | $M/\sigma^{3}$ | kg/m³ |
| Diffusion | $\sigma^{2}/\tau$ | m²/s |

## 3. Construction sequence

`LJUnits(inputs)` performs these steps in order:

1. `SIInput` has already checked that physical values are positive, counts are at least 1, and $0 \le N_\text{eq} < N_\text{iter}$.
2. Build `SIUnits` from $\sigma$, $\epsilon$ and $M_\text{mol}$. This is the only place the formulas live.
3. Convert the mass density to the reduced density $\rho^*$, then compute $N = 4n^3$ and $L_\text{box} = (N/\rho^*)^{1/3}$.
4. Check $r_c < L_\text{box}/2$ and raise `ValueError` otherwise.
5. Build `Reduced` and store it. The object is frozen, so nothing changes afterwards.

## 4. Public API

| Call | Use |
|---|---|
| `LJUnits(inputs)` | Start of a run |
| `LJUnits.from_mapping(attrs)` | Start of analysis (HDF5 attributes) |
| `units.reduced` | Passed to the simulation |
| `units.scales` | Inspect any unit scale |
| `units.scales.table()` | Print all scales in SI |
| `units.to_si(name, x)` | Reduced → SI for any observable |
| `units.to_reduced(name, x)` | SI → reduced |
| `units.label(name, system)` | Axis labels |
| `asdict(units.inputs)` | Attributes to write to HDF5 |

## 5. Usage

Setting up a run:

```python
inputs = SIInput(temperature=90.0, mass_density=1374.0, n_cells=4)
units = LJUnits(inputs)
sim = HMC(units.reduced)   # physics sees reduced values only
```

During a run:

```python
for k, _ in enumerate(sim.run()):
    if k % 1000 == 0:
        T = units.to_si("T", sim.history.last("T"))
        print(f"{k}: T = {T:.2f} K")
```

Saving:

```python
attrs = {k: v for k, v in asdict(inputs).items() if v is not None}
f.attrs.update(attrs)      # reduced datasets go under /history
```

Analysis:

```python
with h5py.File("run.h5") as f:
    units = LJUnits.from_mapping(f.attrs)
    P_pa = units.to_si("P", f["history/P"][:])
    print(units.label("P", "si"))
```

## 6. HDF5 details

- HDF5 attributes cannot hold `None`, so an unset `seed` is omitted when writing and treated as missing when reading.
- h5py returns NumPy scalars. `from_mapping` casts integer fields with `int` and all others with `float`.
- Optionally store the derived scales in a `/units` group and compare with the recomputed values on load, to detect a changed formula between runs.
- Store a `schema_version` attribute so future format changes can be handled explicitly.

## 7. Testing checklist

- [ ] Round trip `to_reduced(to_si(x)) == x` for every entry in `QUANTITIES`
- [ ] For argon, $\tau \approx 2.15$ ps
- [ ] `SIInput.from_mapping(asdict(x)) == x`
- [ ] A missing required key raises `KeyError`
- [ ] An oversized `r_cut` raises `ValueError`
- [ ] `mypy --strict` passes

## 8. Open decision

Whether the numerical settings ($\Delta t$, $N_\text{steps}$, $N_\text{iter}$, $N_\text{eq}$, seed) stay in `Reduced` as pass-through values, so the simulation takes a single object, or remain only in `SIInput`.
