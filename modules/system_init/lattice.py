from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from modules.system_init.system import SimulationParameters

# The 4 atoms of one cubic FCC cell (fractional coordinates): one at the
# corner and one at the centre of each of three faces.
_FCC_BASIS = np.array(
    [[0.0, 0.0, 0.0], [0.5, 0.5, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.5]]
)


def fcc(parameters: SimulationParameters) -> NDArray[np.float64]:
    """
    Place N = 4 * n_cells**3 particles on an FCC lattice in a periodic cube.

    Everything is read from ``parameters`` in reduced units, so no unit
    conversion happens here. The box length is ``parameters.l_box_red``
    (or ``parameters.l_box_SI``); it is not returned separately.

    Parameters
    ----------
    parameters : SimulationParameters
        Provides ``n_cells``, ``n_particles``, ``l_box_red``, ``jiggle``
        and ``seed``. ``jiggle`` is the maximum random displacement per
        coordinate as a fraction of the cell edge ``a = L / n_cells``; 0.0
        gives a perfect lattice.

    Returns
    -------
    positions : ndarray, shape (N, 3)
        Coordinates in units of sigma, wrapped into ``[0, L)``.
    """
    n = parameters.n_cells
    box = parameters.l_box_red
    a = box / n  # cubic cell edge in sigma

    # Cell indices (i, j, k), shape (n^3, 1, 3); broadcasts against the
    # basis (4, 3) -> (n^3, 4, 3).
    grid = np.arange(n)
    cells = np.stack(np.meshgrid(grid, grid, grid, indexing="ij"), axis=-1).reshape(
        -1, 1, 3
    )
    positions = ((cells + _FCC_BASIS) * a).reshape(-1, 3)

    if positions.shape[0] != parameters.n_particles:
        raise RuntimeError("Lattice particle count does not match parameters.")

    if parameters.jiggle > 0:
        rng = np.random.default_rng(parameters.seed)
        positions += rng.uniform(
            -parameters.jiggle * a, parameters.jiggle * a, size=positions.shape
        )
        positions %= box
        positions[positions >= box] = 0.0  # guard against float rounding to L

    return positions  # pyright: ignore[reportReturnType]
