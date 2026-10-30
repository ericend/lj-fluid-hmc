import numpy as np
from numpy.typing import NDArray

AVOGADRO: float = 6.02214076e23  # particles per mol
ANGSTROM3_PER_CM3: float = 1e24  # 1 cm = 1e8 Å, so 1 cm^3 = (1e8)^3 = 1e24 Å^3


def init_fcc(
    N: int,
    density: float,
    molar_mass: float,
    sigma: float,
    jiggle: float = 0.0,
    seed: int | None = None,
) -> tuple[NDArray[np.float64], float, float]:
    """
    Initialize a Lennard-Jones fluid on an FCC lattice from physical density.

    Particles are placed on a face-centred-cubic (FCC) lattice that fills a
    cubic periodic box whose volume reproduces the requested mass density.
    Optionally, a small random displacement is applied to break the lattice
    symmetry. With the default ``jiggle=0.0`` the lattice is perfect.

    Parameters
    ----------
    N : int
        Number of particles. Must equal ``4 * n**3`` for integer ``n``
        (32, 108, 256, 500, 864, ...), because the conventional cubic FCC
        cell contains 4 atoms and the box holds ``n x n x n`` cells.
    density : float
        Target mass density in g/cm³ (e.g. 1.374 for liquid argon at
        approximately 90 K).
    molar_mass : float
        Molar mass in g/mol (e.g. 39.948 for argon).
    sigma : float
        Lennard-Jones sigma in Å (e.g. 3.405 for argon). Returned positions
        are expressed in multiples of this length.
    jiggle : float, optional
        Maximum random displacement per coordinate, as a fraction of the
        FCC cubic cell edge ``a = L / n`` (not of the box side ``L``).
        Each coordinate of each particle is shifted by an independent uniform
        random number in ``[-jiggle * a, +jiggle * a]``. For N=256, ``a`` is
        about 1.69 sigma, so ``jiggle=0.02`` gives at most about 0.034 sigma.
        Default is 0.0, i.e. a perfect FCC lattice.
    seed : int or None, optional
        Seed for ``numpy.random.default_rng``. Default is None
        (non-deterministic). Has no effect if ``jiggle == 0``.

    Returns
    -------
    positions : numpy.ndarray, shape (N, 3)
        Particle coordinates in reduced units (multiples of sigma), wrapped
        into ``[0, box_length_reduced)``.
    box_length_reduced : float
        Cubic box side length in units of sigma.
    box_length_angstrom : float
        Cubic box side length in Å.

    Raises
    ------
    ValueError
        If ``N`` is not of the form ``4 * n**3``, or if any physical input
        is non-positive.
    RuntimeError
        If the final reduced density does not match the closed-form value
        (sanity check against unit mistakes).

    Notes
    -----
    The reduced number density is
    ``rho* = N * sigma**3 / V = density * N_A * sigma**3 / molar_mass``.

    The nearest-neighbour distance on the lattice is ``a / sqrt(2)``, where
    ``a = L / n`` is the cubic cell edge (12 neighbours per atom).

    A perfect lattice has zero net force on every atom by symmetry; it only
    evolves once momenta are drawn (MD or HMC).

    Examples
    --------
    >>> pos, L_red, L_A = init_lj_fluid_fcc(256, 1.396, 39.948, 3.405)
    >>> pos.shape
    (256, 3)
    >>> round(L_A, 1)
    23.0
    """
    if min(density, molar_mass, sigma) <= 0 or N <= 0:
        raise ValueError("N, density, molar_mass and sigma must be positive.")

    # Cells per box edge: N = 4 * n^3  ->  n = (N/4)^(1/3). round() absorbs
    # floating-point error; the check below verifies the result is exact.
    n_cells = round((N / 4) ** (1.0 / 3.0))
    if 4 * n_cells**3 != N:
        raise ValueError(
            f"N={N} is not a valid FCC count (4*n^3): 32, 108, 256, 500, 864, ..."
        )

    # Box size from mass density: V = mass / density, L = V^(1/3).
    volume_A3 = (N / AVOGADRO) * molar_mass / density * ANGSTROM3_PER_CM3
    box_length_angstrom = volume_A3 ** (1.0 / 3.0)
    box_length_reduced = box_length_angstrom / sigma
    a = box_length_reduced / n_cells  # cubic cell edge in sigma

    # The 4 atoms of one cubic FCC cell (fractional coordinates): one at the
    # corner and one at the centre of each of three faces.
    basis = np.array(
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.5]]
    )

    # Cell indices (i, j, k), shape (n^3, 1, 3). The extra axis broadcasts
    # against basis (4, 3) -> (n^3, 4, 3).
    grid = np.arange(n_cells)
    cells = np.stack(np.meshgrid(grid, grid, grid, indexing="ij"), axis=-1).reshape(
        -1, 1, 3
    )
    positions = ((cells + basis) * a).reshape(-1, 3)

    # Symmetry-breaking displacement. With jiggle=0 the range is [0, 0], so
    # uniform() returns exact zeros and the lattice stays perfect.
    rng = np.random.default_rng(seed)
    positions += rng.uniform(-jiggle * a, jiggle * a, size=positions.shape)

    # Periodic wrap: displaced atoms re-enter on the opposite face.
    positions %= box_length_reduced

    # Sanity check: N / L^3 must equal rho* computed directly from the inputs
    # (sigma * 1e-8 converts Å to cm).
    rho_star = density * AVOGADRO * (sigma * 1e-8) ** 3 / molar_mass
    if not np.isclose(N / box_length_reduced**3, rho_star):
        raise RuntimeError("Reduced density mismatch; check inputs/units.")

    return positions, box_length_reduced, box_length_angstrom
