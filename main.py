# region: imports
from datetime import datetime
from pathlib import Path

import h5py

import modules.system_init.system as sys
from analysis.plotting import plot_positions_3d

# endregion

# region: paths
ROOT = Path(__file__).resolve().parent
STAMP = datetime.now().strftime("%Y%m%d_%H%M")
DATA_DIR = ROOT / "results" / "data" / STAMP
PLOTS_DIR = ROOT / "results" / "plots" / STAMP
for folder in (DATA_DIR, PLOTS_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# endregion


def main() -> None:
    # user input
    input = sys.SIInput(
        seed=42
    )  # use std values for now with fixed seed for replicability

    sim_params = sys.SimulationParams(input)
    pos, L_red, _ = sim_params.build_fcc_lattice(jiggle=0.04)
    inputs, derived = sim_params.to_dict()

    with h5py.File(DATA_DIR / "run.hdf5", "x") as f:
        f.attrs["schema_version"] = 1
        f.create_group("inputs").attrs.update(inputs)
        f.create_group("derived").attrs.update(derived)
        f.create_dataset("positions/initial", data=pos)

    print(f"Stamp: {STAMP}")
    print(sim_params.print_parameters())

    fig, _ = plot_positions_3d(pos, L_red, axis_label=r"$\sigma$", view="010")
    fig.savefig(PLOTS_DIR / "positions_yview_jiggle.png")


if __name__ == "__main__":
    main()
