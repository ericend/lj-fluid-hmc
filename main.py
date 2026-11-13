# region: imports
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import h5py
from modules.hmc import HMC

from modules.history import History
from modules.parameters import Input, LJUnits

# endregion

# region: paths
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "results" / "data"
PLOTS_DIR = ROOT / "results" / "plots"
for folder in (DATA_DIR, PLOTS_DIR):
    folder.mkdir(parents=True, exist_ok=True)
# endregion


def main() -> None:

    inputs = Input(
        temperature=90.0,  # K
        mass_density=1374.0,  # kg/m^3
        sigma=3.40e-10,  # m (Å)
        epsilon=1.654e-21,  # J
        molar_mass=39.948e-3,  # kg/mol
        n_cells=4,
        dt=0.004,
        verlet_steps=20,
        r_cut=2.5,
        n_iter=10_000,
        n_eq=1_000,
        seed=None,
    )

    units = LJUnits(inputs)
    sim = HMC(units.reduced)
    history = History()
    for state in sim.run():
        history.record(state)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with h5py.File(DATA_DIR / f"hmc_{stamp}.h5", "x") as f:
        f.attrs.update({k: v for k, v in asdict(inputs).items() if v is not None})
        grp = f.create_group("history")
        for name, values in history.as_dict().items():  # reduced units
            grp.create_dataset(name, data=values)


if __name__ == "__main__":
    main()
