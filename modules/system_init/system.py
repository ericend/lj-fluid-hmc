# system.py
"""
Simulation parameters and SI <-> reduced Lennard-Jones unit conversion.

The simulation engine runs entirely in dimensionless reduced units. The user
specifies everything in SI units through `SIInput`; `SimulationParameters`
validates the input, converts it once, and exposes the results as ``*_red``
properties. The original SI values stay available as ``*_SI`` properties.

Workflow
--------
1. Define the run in an `SIInput` (K, kg/m^3, m, J, kg/mol, s).
2. Build ``params = SimulationParameters(inputs)``.
3. Read reduced values (``params.density_red``, ``params.dt_red``, ...) in the
   simulation loop.
4. Convert results back with the ``convert_*_to_SI`` methods.

Examples
--------
>>> from system import SIInput, SimulationParameters
>>> params = SimulationParameters(SIInput(temperature=90.0, seed=42))
>>> round(params.density_red, 3)
0.814
>>> round(params.l_box_red, 2)
6.8
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Final, TypeVar

import numpy as np
import numpy.typing as npt

K_B: Final[float] = 1.380649e-23  # J/K
N_A: Final[float] = 6.02214076e23  # 1/mol
ZERO_CELSIUS_K: Final[float] = 273.15  # K
SUPPORTED_LATTICES: Final[tuple[str, ...]] = ("FCC",)

# Scalar or array input; the output has the same type as the input
Num = TypeVar("Num", float, npt.NDArray[np.float64])


@dataclass(frozen=True, slots=True, kw_only=True)
class SIInput:
    """
    User-editable simulation input. All physical quantities are in SI units.

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
    dt : float, default: 8.6e-15
        Velocity Verlet time step, in s (about 0.004 tau for argon).
    r_cut : float, default: 8.5e-10
        Force and energy cutoff radius, in m (2.5 sigma for argon).
    n_cells : int, default: 4
        Number of unit cells per box side (N = 4 * n_cells**3 for FCC).
    lattice : str, default: "FCC"
        Initial lattice type. Currently only "FCC".
    jiggle : float, default: 0.0
        Maximum random initial displacement per coordinate, as a fraction of
        the cubic cell edge. 0.0 gives a perfect lattice.
    verlet_steps : int, default: 20
        Velocity Verlet steps per HMC trajectory.
    n_iter : int, default: 10000
        Total number of HMC iterations (trajectories).
    n_eq : int, default: 1000
        Initial iterations discarded as equilibration.
    seed : int or None, default: None
        Seed for the random number generator.
    """

    temperature: float = 90.0  # K
    mass_density: float = 1374.0  # kg/m^3
    sigma: float = 3.40e-10  # m
    epsilon: float = 1.654e-21  # J
    molar_mass: float = 39.948e-3  # kg/mol
    dt: float = 8.6e-15  # s
    r_cut: float = 8.5e-10  # m
    n_cells: int = 4
    lattice: str = "FCC"
    jiggle: float = 0.0
    verlet_steps: int = 20
    n_iter: int = 10_000
    n_eq: int = 1_000
    seed: int | None = None

    def __post_init__(self) -> None:
        positive = (
            self.temperature,
            self.mass_density,
            self.sigma,
            self.epsilon,
            self.molar_mass,
            self.dt,
            self.r_cut,
        )
        if min(positive) <= 0:
            raise ValueError("All physical parameters, dt, and r_cut must be positive.")
        if min(self.n_cells, self.verlet_steps, self.n_iter) < 1:
            raise ValueError("n_cells, verlet_steps, and n_iter must be >= 1.")
        if not 0 <= self.n_eq < self.n_iter:
            raise ValueError("n_eq must satisfy 0 <= n_eq < n_iter.")
        if self.jiggle < 0:
            raise ValueError("jiggle must be non-negative.")
        if self.lattice not in SUPPORTED_LATTICES:
            raise ValueError(
                f"lattice must be one of {SUPPORTED_LATTICES}, got {self.lattice!r}."
            )


class SimulationParameters:
    """
    Holds the SI inputs, the derived reduced quantities, and unit converters.

    Naming convention: a property ending in ``_SI`` is in SI units, one ending
    in ``_red`` is dimensionless (reduced LJ units).

    Parameters
    ----------
    inputs : SIInput
        Validated user input in SI units.
    """

    def __init__(self, inputs: SIInput) -> None:
        self._inputs = inputs

        # Unit scales
        self._mass_SI = inputs.molar_mass / N_A
        self._tau_SI = inputs.sigma * math.sqrt(self._mass_SI / inputs.epsilon)
        self._velocity_unit_SI = math.sqrt(inputs.epsilon / self._mass_SI)

        # Reduced state
        self._n_particles = 4 * inputs.n_cells**3
        self._density_red = self.convert_density_to_red(inputs.mass_density)
        self._temperature_red = self.convert_temp_to_red(inputs.temperature)
        self._l_box_red = (self._n_particles / self._density_red) ** (1 / 3)
        self._dt_red = self.convert_time_to_red(inputs.dt)
        self._r_cut_red = self.convert_length_to_red(inputs.r_cut)

        if self._r_cut_red >= self._l_box_red / 2:
            raise ValueError(
                f"r_cut={self._r_cut_red:.3f} sigma must be < L_box/2="
                f"{self._l_box_red / 2:.3f} sigma; increase n_cells or reduce r_cut."
            )

    def print_parameters(self) -> None:
        """Print all simulation parameters, derived scales, and settings."""
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
Time Step           : {self.dt_SI:>12.4e}  [s]
Cutoff              : {self.r_cut_SI:>12.4e}  [m]
Box Length          : {self.l_box_SI:>12.4e}  [m]

[2] Reduced State Properties (Dimensionless)
--------------------------------------------------------------------
Temperature (T*)    : {self.temperature_red:>12.4f}  [-]
Density (rho*)      : {self.density_red:>12.4f}  [-]
Box Length (L*)     : {self.l_box_red:>12.4f}  [-]
Time Step (dt*)     : {self.dt_red:>12.4f}  [-]
Cutoff (r_cut*)     : {self.r_cut_red:>12.4f}  [-]

[3] Simulation Settings
--------------------------------------------------------------------
Lattice             : {self.lattice:>12}
Lattice Jiggle      : {self.jiggle:>12.4f}
Unit Cells (1D)     : {self.n_cells:>12}
Total Particles     : {self.n_particles:>12}
Verlet Steps/Traj   : {self.verlet_steps:>12}
Total Iterations    : {self.n_iter:>12}
Eq. Iterations      : {self.n_eq:>12}
RNG Seed            : {self.seed!s:>12}
====================================================================
"""
        print(summary.strip())

    def to_dict(self) -> tuple[dict[str, Any], dict[str, float | int]]:
        """
        Collect all parameters as flat dicts.

        Returns
        -------
        inputs : dict
            Exactly the `SIInput` fields, so ``SIInput(**inputs)`` recreates
            the run. A seed of ``None`` is omitted because HDF5 attributes
            cannot store ``None``.
        derived : dict
            Unit scales and reduced values computed from the inputs. For
            reference only; they can be recomputed from ``inputs``.
        """
        inputs = {k: v for k, v in asdict(self._inputs).items() if v is not None}
        derived: dict[str, float | int] = {
            "mass_SI": self.mass_SI,
            "tau_SI": self.tau_SI,
            "velocity_unit_SI": self.velocity_unit_SI,
            "l_box_SI": self.l_box_SI,
            "n_particles": self.n_particles,
            "temperature_red": self.temperature_red,
            "density_red": self.density_red,
            "l_box_red": self.l_box_red,
            "dt_red": self.dt_red,
            "r_cut_red": self.r_cut_red,
        }
        return inputs, derived

    # ==========================================
    # 1. SI PROPERTIES
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
    def dt_SI(self) -> float:
        return self._inputs.dt

    @property
    def r_cut_SI(self) -> float:
        return self._inputs.r_cut

    @property
    def mass_SI(self) -> float:
        return self._mass_SI

    @property
    def tau_SI(self) -> float:
        return self._tau_SI

    @property
    def velocity_unit_SI(self) -> float:
        return self._velocity_unit_SI

    @property
    def l_box_SI(self) -> float:
        return self.convert_length_to_SI(self._l_box_red)

    # ==========================================
    # 2. REDUCED PROPERTIES
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
        return self._dt_red

    @property
    def r_cut_red(self) -> float:
        return self._r_cut_red

    # ==========================================
    # 3. COUNTS AND NUMERICAL SETTINGS
    # ==========================================
    @property
    def n_cells(self) -> int:
        return self._inputs.n_cells

    @property
    def n_particles(self) -> int:
        return self._n_particles

    @property
    def lattice(self) -> str:
        return self._inputs.lattice

    @property
    def jiggle(self) -> float:
        return self._inputs.jiggle

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
ARGON: Final[SimulationParameters] = SimulationParameters(SIInput())
