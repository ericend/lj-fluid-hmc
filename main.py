# region: imports
from datetime import datetime
from pathlib import Path

import h5py

import modules.system_init.system as sys
from analysis.plotting import plot_positions_3d
from modules.system_init import lattice

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
    # user input in SI units
    input = sys.SIInput(seed=42)
    parameters = sys.SimulationParameters(input)
    inputs, derived = parameters.to_dict()
    start_positions = lattice.fcc(parameters=parameters)
    with h5py.File(DATA_DIR / "run.hdf5", "x") as f:
        f.attrs["schema_version"] = 1
        f.create_group("inputs").attrs.update(inputs)
        f.create_group("derived").attrs.update(derived)
        f.create_dataset("positions/initial", data=start_positions)

    print(f"Stamp: {STAMP}")
    print(parameters.print_parameters())

    fig, _ = plot_positions_3d(
        start_positions, parameters.l_box_red, axis_label=r"$\sigma$", view="010"
    )
    fig.savefig(PLOTS_DIR / "positions_yview_jiggle.png")


if __name__ == "__main__":
    main()
