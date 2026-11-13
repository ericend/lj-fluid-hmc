# system.py
"""
Simulation parameters, reduced Lennard-Jones units, and FCC lattice initialization.

This module provides the core configuration and unit conversion system for
the HMC simulation. The simulation engine runs entirely in dimensionless
reduced units. This module acts as the bridge between human-readable SI
inputs and the simulation core.

Workflow
--------
1. Define the physical and numerical settings in an `SIInput` dataclass.
2. Initialize `SimulationParams(inputs)` to validate the configuration and
   compute all reduced scales.
3. Generate the starting configuration using `SimulationParams.build_fcc_lattice()`.
4. Read reduced state properties (e.g., `density_red`, `temperature_red`)
   directly from the `SimulationParams` instance for the simulation loop.
5. Convert results back to SI using the `convert_*_to_SI` methods.

Classes
-------
SIInput
    Frozen, keyword-only dataclass containing user-editable simulation parameters
    in strict SI units (K, kg/m^3, m, J, kg/mol).
SimulationParams
    Unified parameter manager providing access to SI inputs, reduced system
    state variables, unit converters, and FCC lattice generation.

Functions
---------
celsius_to_kelvin
    Utility to convert Celsius to Kelvin.
kelvin_to_celsius
    Utility to convert Kelvin to Celsius.

Examples
--------
>>> from system import SIInput, SimulationParams
>>> inputs = SIInput(temperature=90.0, mass_density=1374.0, seed=42)
>>> sim_params = SimulationParams(inputs)
>>> positions, L_red, L_A = sim_params.build_fcc_lattice(jiggle=0.01)
>>> print(f"Reduced density: {sim_params.density_red:.3f}")
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Final, TypeVar

import numpy as np
import numpy.typing as npt

from modules.system_init.FCC_lattice_init import init_fcc

K_B: Final[float] = 1.380649e-23  # J/K
N_A: Final[float] = 6.02214076e23  # 1/mol
ZERO_CELSIUS_K: Final[float] = 273.15  # K

# Scalar or array input; the output has the same type as the input
Num = TypeVar("Num", float, npt.NDArray[np.float64])


@dataclass(frozen=True, slots=True, kw_only=True)
class SIInput:
    """
    User-editable simulation input in SI units.

    Physical quantities are given in SI units. Numerical settings are
    already dimensionless (reduced units) and are passed through unchanged.
    All fields are keyword-only, and the dataclass instance is immutable.

    Parameters
    ----------
    temperature : float, default: 90.0
        Target temperature of the canonical ensemble, in K.
    mass_density : float, default: 1374.0
        Mass density of the fluid, in kg/m^3.
    sigma : float, default: 3.40e-10
        Lennard-Jones length parameter, in m.
    epsilon : float, default: 1.654e-21
        Lennard-Jones well depth, in J.
    molar_mass : float, default: 39.948e-3
        Molar mass of the substance, in kg/mol.
    n_cells : int, default: 4
        Number of FCC unit cells per box side.
    dt : float, default: 0.004
        Velocity Verlet time step, in reduced time units.
    verlet_steps : int, default: 20
        Number of Velocity Verlet steps per HMC trajectory.
    r_cut : float, default: 2.5
        Force and energy cutoff, in units of sigma.
    n_iter : int, default: 10000
        Total number of HMC iterations (trajectories).
    n_eq : int, default: 1000
        Number of initial iterations discarded as equilibration.
    seed : int or None, default: None
        Seed for the random number generator.
    """

    temperature: float = 90.0  # K
    mass_density: float = 1374.0  # kg/m^3
    sigma: float = 3.40e-10  # m
    epsilon: float = 1.654e-21  # J
    molar_mass: float = 39.948e-3  # kg/mol
    n_cells: int = 4
    dt: float = 0.004
    verlet_steps: int = 20
    r_cut: float = 2.5
    n_iter: int = 10_000
    n_eq: int = 1_000
    seed: int | None = None

    def __post_init__(self) -> None:
        pos = (
            self.temperature,
            self.mass_density,
            self.sigma,
            self.epsilon,
            self.molar_mass,
            self.dt,
            self.r_cut,
        )
        if min(pos) <= 0:
            raise ValueError("Physical parameters, dt, and r_cut must be positive.")
        if min(self.n_cells, self.verlet_steps, self.n_iter) < 1:
            raise ValueError("n_cells, verlet_steps, and n_iter must be >= 1.")
        if not 0 <= self.n_eq < self.n_iter:
            raise ValueError("n_eq must satisfy 0 <= n_eq < n_iter.")


class SimulationParams:
    """
    Unified class holding SI inputs, reduced system properties, and unit converters.

    Parameters
    ----------
    inputs : SIInput
        Validated user input containing physical quantities in SI units and
        dimensionless simulation settings.
    """

    def __init__(self, inputs: SIInput) -> None:
        self._inputs = inputs

        self._mass_SI = inputs.molar_mass / N_A
        self._tau_SI = inputs.sigma * math.sqrt(self._mass_SI / inputs.epsilon)
        self._velocity_unit_SI = math.sqrt(inputs.epsilon / self._mass_SI)

        self._n_particles = 4 * inputs.n_cells**3
        self._density_red = self.convert_density_to_red(inputs.mass_density)
        self._l_box_red = (self._n_particles / self._density_red) ** (1 / 3)
        self._temperature_red = self.convert_temp_to_red(inputs.temperature)

        if inputs.r_cut >= self._l_box_red / 2:
            raise ValueError(
                f"r_cut={inputs.r_cut} must be < L_box/2={self._l_box_red / 2:.3f}; "
                "increase n_cells or reduce r_cut."
            )

    def print_parameters(self) -> None:
        """Print all simulation parameters, derived scales, and dimensionless settings."""
        summary = f"""
====================================================================
                    SIMULATION PARAMETERS
====================================================================
[1] SI State & Scales
--------------------------------------------------------------------
Temperature         : {self.temperature_SI:>12.4e}  [K]
Mass Density        : {self.density_SI:>12.4e}  [kg/m^3]
Sigma               : {self.sigma_SI:>12.4e}  [m]
Epsilon             : {self.epsilon_SI:>12.4e}  [J]
Molar Mass          : {self.molar_mass_SI:>12.4e}  [kg/mol]
Mass (single atom)  : {self.mass_SI:>12.4e}  [kg]
Time Unit (Tau)     : {self.tau_SI:>12.4e}  [s]
Velocity Unit       : {self.velocity_unit_SI:>12.4e}  [m/s]

[2] Reduced State Properties (Dimensionless)
--------------------------------------------------------------------
Temperature (T*)    : {self.temperature_red:>12.4f}  [-]
Density (rho*)      : {self.density_red:>12.4f}  [-]
Box Length (L*)     : {self.l_box_red:>12.4f}  [-]
Time Step (dt*)     : {self.dt_red:>12.4f}  [-]
Cutoff (r_cut*)     : {self.r_cut_red:>12.4f}  [-]

[3] Simulation Settings (Dimensionless)
--------------------------------------------------------------------
Unit Cells (1D)     : {self.n_cells:>12}
Total Particles     : {self.n_particles:>12}
Verlet Steps/Traj   : {self.verlet_steps:>12}
Total Iterations    : {self.n_iter:>12}
Eq. Iterations      : {self.n_eq:>12}
RNG Seed            : {self.seed!s:>12}
====================================================================
"""
        print(summary.strip())

    def build_fcc_lattice(
        self, jiggle: float = 0.0
    ) -> tuple[npt.NDArray[np.float64], float, float]:
        """
        Initialize the FCC lattice using the external `init_fcc` function.

        Automatically converts strict SI inputs (kg/m^3, kg/mol, m) to the
        chemistry units (g/cm^3, g/mol, Å) expected by the lattice generator.

        Parameters
        ----------
        jiggle : float, default: 0.0
            Maximum random displacement per coordinate as a fraction of the
            FCC cubic cell edge.

        Returns
        -------
        positions : ndarray
            Particle coordinates in reduced units, shape (N, 3).
        box_length_reduced : float
            Box length in reduced units.
        box_length_angstrom : float
            Box length in Angstroms.
        """
        density_g_cm3 = self.density_SI * 1e-3
        molar_mass_g_mol = self.molar_mass_SI * 1000.0
        sigma_angstrom = self.sigma_SI * 1e10

        return init_fcc(
            N=self.n_particles,
            density=density_g_cm3,
            molar_mass=molar_mass_g_mol,
            sigma=sigma_angstrom,
            jiggle=jiggle,
            seed=self.seed,
        )

    def to_dict(self) -> tuple[dict, dict]:
        """
        Collect all parameters in a plain dict.

        Returns
        -------
        dict
            Two sections of flat ``{name: number}`` dicts:

            ``"inputs"``
                Exactly the `SIInput` fields, so that ``SIInput(**inputs)``
                recreates the run. A seed of ``None`` is omitted because HDF5
                attributes cannot store ``None``.
            ``"derived"``
                Unit scales and reduced state values computed from the inputs.
                These are for reference and can be recomputed from ``inputs``.
        """

        inputs = {k: v for k, v in asdict(self._inputs).items() if v is not None}
        derived: dict[str, float | int] = {
            "mass_SI": self.mass_SI,
            "tau_SI": self.tau_SI,
            "velocity_unit_SI": self.velocity_unit_SI,
            "n_particles": self.n_particles,
            "temperature_red": self.temperature_red,
            "density_red": self.density_red,
            "l_box_red": self.l_box_red,
        }
        return inputs, derived

    # ==========================================
    # 1. SYSTEM STATE PROPERTIES (SI)
    # ==========================================

    @property
    def temperature_SI(self) -> float:
        return self._inputs.temperature

    @property
    def density_SI(self) -> float:
        return self._inputs.mass_density

    @property
    def sigma_SI(self) -> float:
        return self._inputs.sigma

    @property
    def epsilon_SI(self) -> float:
        return self._inputs.epsilon

    @property
    def molar_mass_SI(self) -> float:
        return self._inputs.molar_mass

    @property
    def mass_SI(self) -> float:
        return self._mass_SI

    @property
    def tau_SI(self) -> float:
        return self._tau_SI

    @property
    def velocity_unit_SI(self) -> float:
        return self._velocity_unit_SI

    # ==========================================
    # 2. SYSTEM STATE PROPERTIES (Reduced)
    # ==========================================
    @property
    def temperature_red(self) -> float:
        return self._temperature_red

    @property
    def density_red(self) -> float:
        return self._density_red

    @property
    def l_box_red(self) -> float:
        return self._l_box_red

    @property
    def dt_red(self) -> float:
        return self._inputs.dt

    @property
    def r_cut_red(self) -> float:
        return self._inputs.r_cut

    # ==========================================
    # 3. SYSTEM STATE PROPERTIES (Counts)
    # ==========================================
    @property
    def n_cells(self) -> int:
        return self._inputs.n_cells

    @property
    def n_particles(self) -> int:
        return self._n_particles

    @property
    def verlet_steps(self) -> int:
        return self._inputs.verlet_steps

    @property
    def n_iter(self) -> int:
        return self._inputs.n_iter

    @property
    def n_eq(self) -> int:
        return self._inputs.n_eq

    @property
    def seed(self) -> int | None:
        return self._inputs.seed

    # ==========================================
    # 4. CONVERTERS: SI -> Reduced
    # ==========================================

    def convert_length_to_red(self, r: Num) -> Num:
        return r / self.sigma_SI

    def convert_energy_to_red(self, energy: Num) -> Num:
        return energy / self.epsilon_SI

    def convert_temp_to_red(self, temp: Num) -> Num:
        return K_B * temp / self.epsilon_SI

    def convert_time_to_red(self, t: Num) -> Num:
        return t / self.tau_SI

    def convert_mass_to_red(self, m: Num) -> Num:
        return m / self.mass_SI

    def convert_force_to_red(self, force: Num) -> Num:
        return force * self.sigma_SI / self.epsilon_SI

    def convert_density_to_red(self, rho_m: Num) -> Num:
        return rho_m * N_A * self.sigma_SI**3 / self.molar_mass_SI

    def convert_pressure_to_red(self, p: Num) -> Num:
        return p * self.sigma_SI**3 / self.epsilon_SI

    def convert_velocity_to_red(self, v: Num) -> Num:
        return v / self.velocity_unit_SI

    # ==========================================
    # 5. CONVERTERS: Reduced -> SI
    # ==========================================
    def convert_length_to_SI(self, r: Num) -> Num:
        return r * self.sigma_SI

    def convert_energy_to_SI(self, energy: Num) -> Num:
        return energy * self.epsilon_SI

    def convert_temp_to_SI(self, temp: Num) -> Num:
        return temp * self.epsilon_SI / K_B

    def convert_time_to_SI(self, t: Num) -> Num:
        return t * self.tau_SI

    def convert_mass_to_SI(self, m: Num) -> Num:
        return m * self.mass_SI

    def convert_force_to_SI(self, force: Num) -> Num:
        return force * self.epsilon_SI / self.sigma_SI

    def convert_density_to_SI(self, rho: Num) -> Num:
        return rho * self.molar_mass_SI / (N_A * self.sigma_SI**3)

    def convert_pressure_to_SI(self, p: Num) -> Num:
        return p * self.epsilon_SI / self.sigma_SI**3

    def convert_velocity_to_SI(self, v: Num) -> Num:
        return v * self.velocity_unit_SI


def celsius_to_kelvin(temp_c: Num) -> Num:  # noqa: UP047
    return temp_c + ZERO_CELSIUS_K


def kelvin_to_celsius(temp_k: Num) -> Num:  # noqa: UP047
    return temp_k - ZERO_CELSIUS_K


# Default implementation example
ARGON: Final[SimulationParams] = SimulationParams(
    SIInput(
        sigma=3.40e-10,  # m (3.40 Å)
        epsilon=1.654e-21,  # J (CRC, 88th ed.)
        molar_mass=39.948e-3,  # kg/mol (39.948 u)
    )
)
