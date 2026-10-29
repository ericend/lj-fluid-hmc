from pathlib import Path
import h5py
import numpy as np


class SimulationLogger:
    def __init__(
        self,
        output_dir: str,
        filename: str,
        n_particles: int,
        mode: str = "outer",
        params: dict = None,
    ):
        """
        Parameters:
        -----------
        output_dir : Directory path where the file will be saved.
        filename   : Output HDF5 filename (e.g., 'lj_fluid_run.h5').
        n_particles: Number of particles in the fluid (N).
        mode       : 'outer' (HMC trajectory endpoints) or 'all' (inner MD steps included).
        params     : Dictionary of physical parameters (N, T*, density, dt, etc.).
        """
        self.filepath = Path(output_dir) / filename
        self.n_particles = n_particles
        self.mode = mode.lower()
        self.params = params or {}

        if self.mode not in ["outer", "all"]:
            raise ValueError("Mode must be either 'outer' or 'all'")

        # Counters for dataset indexing
        self.outer_count = 0
        self.inner_count = 0

    def __enter__(self):
        # Create output directory if it doesn't exist
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Open HDF5 file
        self.file = h5py.File(self.filepath, "w")

        # Save simulation metadata as HDF5 root attributes
        for key, val in self.params.items():
            self.file.attrs[key] = val
        self.file.attrs["logging_mode"] = self.mode

        # Group 1: Outer Trajectories (always created)
        self.g_outer = self.file.create_group("outer_trajectories")
        self.dset_outer_pos = self.g_outer.create_dataset(
            "positions",
            shape=(0, self.n_particles, 3),
            maxshape=(None, self.n_particles, 3),
            dtype="f8",
            chunks=(100, self.n_particles, 3),
        )
        self.dset_outer_U = self.g_outer.create_dataset(
            "potential_energy", shape=(0,), maxshape=(None,), dtype="f8"
        )
        self.dset_accepted = self.g_outer.create_dataset(
            "accepted", shape=(0,), maxshape=(None,), dtype="bool"
        )

        # Group 2: Inner MD Steps (only populated if mode == 'all')
        if self.mode == "all":
            self.g_inner = self.file.create_group("inner_steps")
            self.dset_inner_pos = self.g_inner.create_dataset(
                "positions",
                shape=(0, self.n_particles, 3),
                maxshape=(None, self.n_particles, 3),
                dtype="f8",
                chunks=(500, self.n_particles, 3),
            )
            self.dset_inner_U = self.g_inner.create_dataset(
                "potential_energy", shape=(0,), maxshape=(None,), dtype="f8"
            )

        return self

    def log_inner(self, r_coords: np.ndarray, U: float):
        """Log an inner Velocity Verlet integration step."""
        if self.mode != "all":
            return  # Silently skip if animation/inner logging is disabled

        self.inner_count += 1
        self.dset_inner_pos.resize((self.inner_count, self.n_particles, 3))
        self.dset_inner_U.resize((self.inner_count,))

        self.dset_inner_pos[self.inner_count - 1] = r_coords
        self.dset_inner_U[self.inner_count - 1] = U

    def log_outer(self, r_coords: np.ndarray, U: float, accepted: bool):
        """Log the state at the end of an HMC trajectory after Metropolis check."""
        self.outer_count += 1
        self.dset_outer_pos.resize((self.outer_count, self.n_particles, 3))
        self.dset_outer_U.resize((self.outer_count,))
        self.dset_accepted.resize((self.outer_count,))

        self.dset_outer_pos[self.outer_count - 1] = r_coords
        self.dset_outer_U[self.outer_count - 1] = U
        self.dset_accepted[self.outer_count - 1] = accepted

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.flush()
        self.file.close()
