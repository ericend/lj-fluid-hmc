r"""3D visualization of particle positions in a cubic periodic box.

The main entry point is :func:`plot_positions_3d`. It returns the figure and
axes, so the caller decides whether to show or save the result.

Selecting the viewing direction
-------------------------------
Pass ``view`` to look along a crystallographic direction. The camera then
uses an orthographic projection, so lattice planes are not distorted by
perspective.

====== ============================== =====================================
view   Camera looks along             Typical use
====== ============================== =====================================
"100"  x axis                         Square pattern of the FCC lattice
"010"  y axis                         Same as "100", rotated
"001"  z axis                         Same as "100", rotated
"110"  face diagonal                  Rectangular pattern
"111"  body diagonal                  Close-packed (hexagonal) layers
None   free (``elev``, ``azim``)      General perspective view (default)
====== ============================== =====================================

Examples
--------
>>> fig, ax = plot_positions_3d(pos, L)                # free perspective
>>> fig, ax = plot_positions_3d(pos, L, view="111")    # close-packed layers
>>> fig, ax = plot_positions_3d(pos, L, elev=30, azim=45)  # custom angle
"""

from itertools import product
from pathlib import Path
from typing import Literal, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from numpy.typing import NDArray

STYLE_FILE = Path(__file__).resolve().parent / "publication.mplstyle"

View = Literal["100", "010", "001", "110", "111"]

# (elevation, azimuth) in degrees for each supported direction
_VIEWS: dict[str, tuple[float, float]] = {
    "100": (0.0, 0.0),
    "010": (0.0, 90.0),
    "001": (90.0, -90.0),
    "110": (0.0, 45.0),
    "111": (float(np.degrees(np.arctan(1 / np.sqrt(2)))), 45.0),
}


def _draw_box(ax: Axes3D, length: float) -> None:
    """Draw the 12 edges of a cubic box with one corner at the origin.

    Parameters
    ----------
    ax : Axes3D
        Axes on which the edges are drawn.
    length : float
        Edge length of the cube, in the same units as the plotted data.

    Notes
    -----
    Two of the 8 corners are joined by an edge exactly when their
    coordinates differ in one component. The line color is taken from
    ``rcParams["axes.edgecolor"]``, so it follows the active style.
    """
    corners = np.array(list(product((0.0, length), repeat=3)))
    for i, a in enumerate(corners):
        for b in corners[i + 1 :]:
            if np.count_nonzero(a != b) == 1:
                ax.plot(
                    *zip(a, b),
                    color=plt.rcParams["axes.edgecolor"],
                    solid_capstyle="round",
                )


def plot_positions_3d(
    positions: NDArray[np.float64],
    box_length: float,
    title: str | None = None,
    axis_label: str = "reduced units",
    ax: Axes3D | None = None,
    elev: float = 20.0,
    azim: float = -55.0,
    view: View | None = None,
) -> tuple[Figure, Axes3D]:
    r"""Plot particle positions in a cubic periodic box.

    Positions are wrapped into the primary cell ``[0, box_length)`` before
    plotting, so unwrapped trajectories are displayed correctly. The figure
    is styled with ``publication.mplstyle`` for the duration of the call
    only, and the global matplotlib settings are left untouched.

    Parameters
    ----------
    positions : ndarray of float64, shape (N, 3)
        Cartesian particle coordinates. They may lie outside the box.
    box_length : float
        Edge length ``L`` of the cubic simulation box, in the same units as
        ``positions``.
    title : str or None, optional
        Axes title. No title is drawn if ``None`` (default), which is usual
        when the LaTeX caption describes the figure.
    axis_label : str, optional
        Unit text appended to the axis labels, e.g. ``"reduced units"``
        (default) or ``r"$\sigma$"``.
    ax : Axes3D or None, optional
        Existing 3D axes to draw on. A new figure with a single 3D axes is
        created if ``None`` (default).
    elev : float, optional
        Camera elevation above the xy-plane, in degrees. Default is 20.
        Ignored if ``view`` is given.
    azim : float, optional
        Camera azimuth in the xy-plane, in degrees. Default is -55.
        Ignored if ``view`` is given.
    view : {"100", "010", "001", "110", "111"} or None, optional
        Crystallographic direction along which the camera looks. If given,
        the preset angles replace ``elev`` and ``azim`` and an orthographic
        projection is used. Default is ``None``, the free perspective view
        set by ``elev`` and ``azim``. See the module docstring for a table
        of the directions.

    Returns
    -------
    fig : Figure
        The figure containing the plot.
    ax : Axes3D
        The 3D axes with the particles and the box edges.

    Raises
    ------
    ValueError
        If ``positions`` does not have shape ``(N, 3)``, or if ``view`` is
        not one of the supported directions.

    Notes
    -----
    The function neither shows nor saves the figure. Call ``plt.show()`` or
    ``fig.savefig(...)`` afterwards. When saving, pass ``dpi`` and
    ``bbox_inches`` explicitly, because the style context has ended by the
    time the function returns.

    The ``view`` presets only reveal structure for ordered configurations,
    such as the initial FCC lattice. In an equilibrated liquid the
    positions look disordered from every direction. Looking along an axis,
    atoms in successive layers overlap and hide one another.

    Examples
    --------
    Default perspective view, saved as a vector graphic:

    >>> fig, ax = plot_positions_3d(pos, L, axis_label=r"$\sigma$")
    >>> fig.savefig("positions.pdf")

    Look along the body diagonal to see the close-packed layers:

    >>> fig, ax = plot_positions_3d(pos, L, view="111")
    """
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError(f"positions must have shape (N, 3), got {positions.shape}")
    if view is not None and view not in _VIEWS:
        raise ValueError(f"view must be one of {sorted(_VIEWS)}, got {view!r}")

    with plt.style.context(STYLE_FILE):
        if ax is None:
            fig = plt.figure()
            ax = cast(Axes3D, fig.add_subplot(projection="3d"))
        else:
            fig = cast(Figure, ax.get_figure())

        wrapped = positions % box_length
        ax.scatter(
            *wrapped.T, s=14, color="C0", edgecolors="white", linewidths=0.3, alpha=0.9
        )
        _draw_box(ax, box_length)

        ticks = [0, box_length / 2, box_length]
        ax.set(
            xlim=(0, box_length),
            ylim=(0, box_length),
            zlim=(0, box_length),
            xticks=ticks,
            yticks=ticks,
            zticks=ticks,
            xlabel=f"$x$ ({axis_label})",
            ylabel=f"$y$ ({axis_label})",
            zlabel=f"$z$ ({axis_label})",
        )
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.set_major_formatter("{x:.1f}")
            # axis.set_pane_color((1, 1, 1, 0))
        ax.set_box_aspect((1, 1, 1))

        if view is not None:
            elev, azim = _VIEWS[view]
            ax.set_proj_type("ortho")
        ax.view_init(elev=elev, azim=azim)

        if title:
            ax.set_title(title)
    return fig, ax
