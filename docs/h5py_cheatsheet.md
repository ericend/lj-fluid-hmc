# h5py Cheat Sheet

Groups work like dictionaries, datasets work like NumPy arrays.

## Files and modes

```python
import h5py, numpy as np

with h5py.File("run.h5", "r") as f:
    ...  # context manager closes the file
```

| Mode | Meaning |
|---|---|
| `"r"` | Read-only, file must exist |
| `"r+"` | Read and write, file must exist |
| `"w"` | Create, overwriting an existing file |
| `"a"` | Read, write, create if missing |
| `"x"` | Create, fail if the file exists |

## Groups

```python
grp = f.create_group("history")
d = f.create_dataset("history/T", ...)  # missing intermediate groups are created
f["history/T"]  # retrieve by path
"history/T" in f  # membership test, full paths work
list(f.keys())
f.items()
f.get("x")  # dictionary-style access
f.visit(print)  # recursive walk over all names
f.visititems(func)  # same, func(name, obj)
```

Iterating over a group yields only its direct members. Use `visit` or `visititems` to walk the whole file.

## Datasets

```python
f.create_dataset("T", data=arr)  # from an existing array
f.create_dataset("T", shape=(100,), dtype="f8")  # empty, fill later
d = f["T"]
d.shape, d.dtype  # inspect without loading data
d[...]  # everything as a NumPy array
d[0]  # single element
d[0:100:10]  # slice, reads only these values
d[...] = arr  # write (file must be open for writing)
```

A dataset is not an array until you slice it. Slicing reads from disk, so browsing large files is cheap.

## Attributes

```python
grp.attrs["temperature"] = 99.5
grp.attrs["temperature"]
"temperature" in grp.attrs
grp.attrs.update({"a": 1, "b": 2.0})
dict(grp.attrs)
```

- Values come back as NumPy scalars; use `.item()` for plain `int`/`float`.
- Attributes cannot store `None`; leave out unset values such as `seed`.

## Useful extras

```python
f.create_dataset("T", data=arr, compression="gzip", compression_opts=4)
f.create_dataset("T", shape=(0,), maxshape=(None,), dtype="f8")  # growable
f["T"].resize((n_new,))
f.flush()
```

`maxshape` enables chunking automatically, and axes set to `None` can grow without limit.

## Organizing a simulation file

### Layout: one array per quantity, not one dataset per frame

Do not create a dataset per trajectory (`pos_0000`, `pos_0001`, ...). Store each quantity as **one** dataset with a leading "frame" axis:

```
run.h5
├─ @schema_version, @created          small run-level metadata
├─ inputs/        (attrs only)        SIInput fields, SI units
├─ derived/       (attrs only)        tau, T*, rho*, L*, ...
├─ initial/
│   └─ positions                      (N, 3)
├─ trajectory/
│   └─ positions                      (n_frames, N, 3)   extendable
└─ observables/
    ├─ T, U, K, P                     (n_frames,)
    └─ accepted                       (n_frames,)
```

Why:

- Every HDF5 object has overhead, and performance reportedly degrades above roughly 50,000 to 100,000 objects. 10,000 iterations would already mean 10,000 datasets.
- One array can be sliced in a single call: `pos[n_eq:]` for production, `pos[::10]` for every tenth frame, `pos[:, 0]` for one particle's path.
- `initial/positions` is a separate dataset because it is written once and has no frame axis.
- Size check: 10,000 frames x 256 particles x 3 x 8 B is about 61 MB.

### Writing with an extendable dataset

h5py datasets are NumPy-like, with no "append row" call. Create the first axis with `maxshape=None` and resize it before each write. Chunks that are too small hurt performance, so chunk several frames together.

```python
n = sim_params.n_particles

with h5py.File(DATA_DIR / "run.h5", "x") as f:
    f.attrs["schema_version"] = 1
    for group, values in sim_params.to_dict().items():  # /inputs, /derived
        f.create_group(group).attrs.update(values)

    f.create_dataset("initial/positions", data=pos0)  # (N, 3)

    traj = f.create_dataset(
        "trajectory/positions",
        shape=(0, n, 3),
        maxshape=(None, n, 3),
        chunks=(100, n, 3),
        dtype="f8",
    )
    names = ("T", "U", "K", "P")
    obs = {
        k: f.create_dataset(
            f"observables/{k}", shape=(0,), maxshape=(None,), chunks=(1000,), dtype="f8"
        )
        for k in names
    }

    for k, state in enumerate(sim.run()):
        traj.resize(k + 1, axis=0)
        traj[k] = state.positions
        for name, ds in obs.items():
            ds.resize(k + 1, axis=0)
            ds[k] = getattr(state, name)
```

Resizing every step is fine at this scale. If it becomes slow, collect 100 frames in a NumPy buffer and write them as one block.

### Handling the simulation parameters

- **Attributes on groups** are the usual home for small scalars that describe the run. Keep them in `/inputs` (what the user set) and `/derived` (what was computed), using `to_dict()`.
- **Store the inputs, not just the results.** `SIInput(**inputs)` recreates the whole run, including `n_eq`, so analysis can do `pos[n_eq:]` without guessing.
- **Keep arrays out of attributes.** Anything array-sized goes in a dataset.
- **Reduced units only in datasets.** Convert to SI at analysis time with `sim_params.convert_*_to_SI`.
- **Wrapped vs unwrapped positions:** diffusion (mean squared displacement) needs positions *without* wrapping into the box. Decide which you store and record it, e.g. `traj.attrs["wrapped"] = False`.
- **Add `schema_version`** so a later layout change can be detected when loading old files.

### Reading back

```python
with h5py.File(path, "r") as f:
    raw = {k: v.item() for k, v in f["inputs"].attrs.items()}
    sim_params = SimulationParams(SIInput(**raw))

    pos0 = f["initial/positions"][...]
    traj = f["trajectory/positions"]
    production = traj[sim_params.n_eq :]  # loads only this part
    T = f["observables/T"][sim_params.n_eq :]
```

Sources: [h5py Quick Start](https://docs.h5py.org/en/stable/quick.html), [h5py Datasets](https://docs.h5py.org/en/stable/high/dataset.html), [HDF5 chunking and performance](https://support.hdfgroup.org/documentation/hdf5/latest/improve_compressed_perf.html)
