# units.py
"""SI input and reduced Lennard-Jones units for HMC simulation.

The simulation core runs entirely in reduced units. This
module handles conversion to dimensionless units and the inverse.

Workflow:
    1. The user edits an :class:`SIInput` in the entry-point script.
    2. ``LJUnits(inputs)`` validates it, builds the simulation box and
       stores the dimensionless values in ``LJUnits.reduced``.
    3. The simulation reads :class:`Reduced` only.
    4. Results are converted back to SI with the ``*_si`` methods.

Classes:
    SIInput: Frozen, keyword-only dataclass with the user-editable values.
        Physical quantities are in SI (K, kg/m^3, m, J, kg/mol). Numerical
        settings (``dt``, ``r_cut``, ``n_steps``, ...) are already reduced.
    Reduced: Frozen dataclass with the dimensionless values the
        simulation uses. ``sigma``, ``epsilon`` and ``mass`` are 1 by
        construction.
    LJUnits: Holds the input, computes ``reduced`` once, and provides
        ``*_red`` (SI -> reduced) and ``*_si`` (reduced -> SI) converters.

Reduced units are built from sigma (length), epsilon (energy) and the
single-atom mass M = molar_mass / N_A:

    ======================  ====================================
    Quantity                Scale
    ======================  ====================================
    Length                  sigma
    Energy                  epsilon
    Temperature             epsilon / k_B
    Time                    tau = sigma * sqrt(M / epsilon)
    Velocity                sqrt(epsilon / M)
    Force                   epsilon / sigma
    Pressure                epsilon / sigma**3
    Number density          sigma**-3
    ======================  ====================================

Conventions:
    - SI inputs: temperature in K, mass density in kg/m^3, pressure in Pa,
      lengths in m, energies in J, times in s.
    - ``M`` is the mass of one atom. The molar mass appears only in
      ``density_red`` and ``density_si``.
    - ``density_red`` takes a mass density and returns the reduced number
      density rho* = N sigma^3 / V.
    - Converters accept a float or a float64 NumPy array and return the
      same type (see ``Num``).
    - Everything is immutable, so the scales cannot change after creation.

Raises:
    ValueError: If an input is non-positive, if ``n_eq >= n_iter``, or if
        the cutoff violates ``r_cut < L_box / 2`` for the chosen box.

Example:
    >>> from units import SIInput, LJUnits
    >>> units = LJUnits(SIInput(temperature=90.0, mass_density=1374.0))
    >>> red = units.reduced
    >>> p_pa = units.pressure_si(0.5)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Final, TypeVar

import numpy as np
import numpy.typing as npt

K_B: Final[float] = 1.380649e-23  # J/K
N_A: Final[float] = 6.02214076e23  # 1/mol
ZERO_CELSIUS_K: Final[float] = 273.15  # K

# Scalar or array input; the output has the same type as the input
Num = TypeVar("Num", float, npt.NDArray[np.float64])


@dataclass(frozen=True, slots=True, kw_only=True)
class Input:
    """User-editable simulation input.

    Physical quantities are given in SI units. Numerical settings are
    already dimensionless (reduced units) and are passed through unchanged.
    All fields are keyword-only and the instance is immutable. Defaults
    correspond to liquid argon at 90 K and 1.374 g/cm^3 (CRC Handbook,
    88th ed.).

    Parameters
    ----------
    temperature : float, default 90.0
        Target temperature of the canonical ensemble, in K. Converted to
        T* = k_B T / epsilon.
    mass_density : float, default 1374.0
        Mass density of the fluid, in kg/m^3. Converted to the reduced
        number density rho* = rho_m N_A sigma^3 / molar_mass, which
        together with ``n_cells`` fixes the box length.
    sigma : float, default 3.40e-10
        Lennard-Jones length parameter, in m.
    epsilon : float, default 1.654e-21
        Lennard-Jones well depth, in J.
    molar_mass : float, default 39.948e-3
        Molar mass of the substance, in kg/mol. The single-atom mass is
        ``molar_mass / N_A``.
    n_cells : int, default 4
        Number of FCC unit cells per box side. The system has
        ``N = 4 * n_cells**3`` particles (256 for the default).
    dt : float, default 0.004
        Velocity Verlet time step, in reduced time units. Typically
        0.002 to 0.005.
    n_steps : int, default 20
        Number of Velocity Verlet steps per HMC trajectory. Typically
        10 to 50.
    r_cut : float, default 2.5
        Force and energy cutoff, in units of sigma. Must satisfy
        ``r_cut < L_box / 2``.
    n_iter : int, default 10_000
        Total number of HMC iterations (trajectories).
    n_eq : int, default 1_000
        Number of initial iterations discarded as equilibration. Must
        satisfy ``0 <= n_eq < n_iter``.
    seed : int or None, default None
        Seed for the random number generator. ``None`` gives a different
        run each time; set an integer for reproducible results.

    Raises
    ------
    ValueError
        If a physical parameter, ``dt`` or ``r_cut`` is not positive, if
        ``n_cells``, ``n_steps`` or ``n_iter`` is less than 1, or if
        ``n_eq`` is outside ``[0, n_iter)``. The check ``r_cut < L_box / 2``
        is made later, in :class:`LJUnits`, because ``L_box`` is not known
        here.

    See Also
    --------
    LJUnits : Validates the input and builds the reduced values.
    Reduced : The dimensionless values used by the simulation.

    Examples
    --------
    >>> inputs = Input(temperature=90.0, n_cells=4, seed=42)
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
            raise ValueError("physical parameters, dt and r_cut must be positive")
        if min(self.n_cells, self.verlet_steps, self.n_iter) < 1:
            raise ValueError("n_cells, n_steps and n_iter must be >= 1")
        if not 0 <= self.n_eq < self.n_iter:
            raise ValueError("n_eq must satisfy 0 <= n_eq < n_iter")


@dataclass(frozen=True, slots=True)
class ReducedUnits:
    """Dimensionless values read by the simulation.

    Attributes
    ----------
    T : float
        Reduced temperature k_B T / epsilon.
    rho : float
        Reduced number density N sigma^3 / V.
    n_particles : int
        Number of particles, ``4 * n_cells**3``.
    l_box : float
        Box side length in units of sigma.
    dt : float
        Velocity Verlet time step (reduced).
    n_steps : int
        Velocity Verlet steps per trajectory.
    r_cut : float
        Cutoff radius in units of sigma.
    n_iter : int
        Total number of HMC iterations.
    n_eq : int
        Number of equilibration iterations.
    seed : int or None
        Random number generator seed.
    sigma, epsilon, mass : float
        Unit scales. Always 1.0 in reduced units; kept for explicitness.
    """

    T: float
    rho: float
    n_particles: int
    l_box: float
    dt: float
    n_steps: int
    r_cut: float
    n_iter: int
    n_eq: int
    seed: int | None
    sigma: float = 1.0
    epsilon: float = 1.0
    mass: float = 1.0


@dataclass(frozen=True, slots=True)
class SIUnits:
    """Reduced-unit scales expressed in SI.

    One reduced unit of each quantity equals the value given here, so
    ``x_si = x_reduced * scale``. The first three fields are the original
    inputs; the rest are derived from them.

    Attributes
    ----------
    sigma : float
        Length unit (input), in m.
    epsilon : float
        Energy unit (input), in J.
    molar_mass : float
        Molar mass (input), in kg/mol.
    mass : float
        Mass of one atom M = molar_mass / N_A, in kg.
    temperature : float
        Temperature unit epsilon / k_B, in K.
    time : float
        Time unit tau = sigma * sqrt(M / epsilon), in s.
    velocity : float
        Velocity unit sqrt(epsilon / M), in m/s.
    force : float
        Force unit epsilon / sigma, in N.
    pressure : float
        Pressure unit epsilon / sigma**3, in Pa.
    number_density : float
        Number density unit sigma**-3, in 1/m^3.
    mass_density : float
        Mass density unit M / sigma**3, in kg/m^3.
    """

    # original
    sigma: float
    epsilon: float
    molar_mass: float
    # derived
    mass: float
    temperature: float
    time: float
    velocity: float
    force: float
    pressure: float
    number_density: float
    mass_density: float


@dataclass(frozen=True, slots=True)
class LJUnits:
    """Reduced-unit scales and SI <-> reduced converters.

    Parameters
    ----------
    inputs : SIInput
        Validated user input. Its ``sigma``, ``epsilon`` and
        ``molar_mass`` define the unit system.

    Attributes
    ----------
    reduced : Reduced
        Dimensionless values for the simulation, computed once at
        construction.

    Raises
    ------
    ValueError
        If ``r_cut >= L_box / 2`` for the box implied by the input.
    """

    inputs: Input
    reduced: Reduced = field(init=False)

    def __post_init__(self) -> None:
        i = self.inputs
        n = 4 * i.n_cells**3
        rho = self.density_red(i.mass_density)
        l_box = (n / rho) ** (1 / 3)
        if i.r_cut >= l_box / 2:
            raise ValueError(
                f"r_cut={i.r_cut} must be < L_box/2={l_box / 2:.3f}; "
                "increase n_cells or reduce r_cut"
            )
        object.__setattr__(
            self,
            "reduced",
            Reduced(
                T=self.temp_red(i.temperature),
                rho=rho,
                n_particles=n,
                l_box=l_box,
                dt=i.dt,
                n_steps=i.n_steps,
                r_cut=i.r_cut,
                n_iter=i.n_iter,
                n_eq=i.n_eq,
                seed=i.seed,
            ),
        )

    # ---------- scales taken from the input ----------
    @property
    def sigma(self) -> float:
        """Length unit in m."""
        return self.inputs.sigma

    @property
    def epsilon(self) -> float:
        """Energy unit in J."""
        return self.inputs.epsilon

    @property
    def molar_mass(self) -> float:
        """Molar mass in kg/mol."""
        return self.inputs.molar_mass

    # ---------- derived scales ----------
    @property
    def mass(self) -> float:
        """Mass M of a single atom in kg."""
        return self.molar_mass / N_A

    @property
    def tau(self) -> float:
        """Time unit sigma * sqrt(M / epsilon) in s."""
        return self.sigma * math.sqrt(self.mass / self.epsilon)

    @property
    def velocity_unit(self) -> float:
        """Velocity unit sqrt(epsilon / M) in m/s."""
        return math.sqrt(self.epsilon / self.mass)

    # ---------- SI -> reduced ----------
    def length_red(self, r: Num) -> Num:
        """Reduced length r*."""
        return r / self.sigma

    def energy_red(self, energy: Num) -> Num:
        """Reduced energy E*."""
        return energy / self.epsilon

    def temp_red(self, temp: Num) -> Num:
        """Reduced temperature T* (temp in K)."""
        return K_B * temp / self.epsilon

    def time_red(self, t: Num) -> Num:
        """Reduced time t*."""
        return t / self.tau

    def mass_red(self, m: Num) -> Num:
        """Reduced mass m* = m / M."""
        return m / self.mass

    def force_red(self, force: Num) -> Num:
        """Reduced force F*."""
        return force * self.sigma / self.epsilon

    def density_red(self, rho_m: Num) -> Num:
        """Reduced number density rho* from mass density (kg/m^3)."""
        return rho_m * N_A * self.sigma**3 / self.molar_mass

    def pressure_red(self, p: Num) -> Num:
        """Reduced pressure p*."""
        return p * self.sigma**3 / self.epsilon

    def velocity_red(self, v: Num) -> Num:
        """Reduced velocity v*."""
        return v / self.velocity_unit

    # ---------- reduced -> SI ----------
    def length_si(self, r: Num) -> Num:
        """Length in m."""
        return r * self.sigma

    def energy_si(self, energy: Num) -> Num:
        """Energy in J."""
        return energy * self.epsilon

    def temp_si(self, temp: Num) -> Num:
        """Temperature in K."""
        return temp * self.epsilon / K_B

    def time_si(self, t: Num) -> Num:
        """Time in s."""
        return t * self.tau

    def mass_si(self, m: Num) -> Num:
        """Mass in kg."""
        return m * self.mass

    def force_si(self, force: Num) -> Num:
        """Force in N."""
        return force * self.epsilon / self.sigma

    def density_si(self, rho: Num) -> Num:
        """Mass density in kg/m^3."""
        return rho * self.molar_mass / (N_A * self.sigma**3)

    def pressure_si(self, p: Num) -> Num:
        """Pressure in Pa."""
        return p * self.epsilon / self.sigma**3

    def velocity_si(self, v: Num) -> Num:
        """Velocity in m/s."""
        return v * self.velocity_unit


def celsius_to_kelvin(temp_c: Num) -> Num:  # noqa: UP047
    """Convert degrees Celsius to kelvin."""
    return temp_c + ZERO_CELSIUS_K


def kelvin_to_celsius(temp_k: Num) -> Num:  # noqa: UP047
    """Convert kelvin to degrees Celsius."""
    return temp_k - ZERO_CELSIUS_K


ARGON: Final[LJUnits] = LJUnits(
    SIInput(
        sigma=3.40e-10,  # m (3.40 Å)
        epsilon=1.654e-21,  # J (CRC, 88th ed.)
        molar_mass=39.948e-3,  # kg/mol (39.948 u)
    )
)
