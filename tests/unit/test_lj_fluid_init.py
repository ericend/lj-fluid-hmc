from typing import Literal

import lj_fluid_init
import numpy as np
import pytest
from lj_fluid_init import AVOGADRO, init_fcc

# Standard argon values
A_DENSITY = 1.374  # g/cm^3, liquid argon ~90 K
A_MOLAR_MASS = 39.948  # g/mol
A_SIGMA = 3.405  # Angstrom
VALID_N = [32, 108, 256, 500]


def make(N=256, **kwargs):
    params = {"density": A_DENSITY, "molar_mass": A_MOLAR_MASS, "sigma": A_SIGMA}
    params.update(kwargs)
    return init_fcc(N, **params)


def min_image(diff, L):
    return diff - L * np.round(diff / L)


def nn_distances(pos, L):
    d = np.linalg.norm(min_image(pos[:, None, :] - pos[None, :, :], L), axis=-1)
    np.fill_diagonal(d, np.inf)
    return d


# ---------- input validation ----------
@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("N", -1),
        ("N", 0),
        ("density", 0),
        ("density", -1),
        ("molar_mass", 0),
        ("molar_mass", -1),
        ("sigma", 0),
        ("sigma", -1),
    ],
)
def test_non_positive_input_raises_value_error(argument, value):
    with pytest.raises(ValueError):
        make(**{argument: value})


@pytest.mark.parametrize("N", [1, 2, 3, 31, 33, 100, 107, 255, 257])
def test_non_fcc_particle_count_raises_value_error(
    N: Literal[1, 2, 3, 31, 33, 100, 107, 255, 257],
):
    with pytest.raises(ValueError, match="not a valid FCC count"):
        make(N)


# ---------- shapes, types, ranges ----------
@pytest.mark.parametrize("N", VALID_N)
def test_output_shape_and_types(N: int):
    pos, L_red, L_A = make(N)
    assert pos.shape == (N, 3)
    assert pos.dtype == np.float64
    assert isinstance(L_red, float)
    assert isinstance(L_A, float)


@pytest.mark.parametrize("jiggle", [0.0, 0.05, 0.3])
def test_positions_wrapped_into_box(jiggle: float):
    pos, L_red, _ = make(256, jiggle=jiggle, seed=1)
    assert np.all(pos >= 0.0)
    assert np.all(pos < L_red)


# ---------- box size and density ----------
def test_argon_256_box_length_matches_hand_calculation():
    # V = 256 * M / (N_A * rho) = ~1.2e4 A^3 for rho = 1.396 g/cm^3 -> L ~ 23.0 A
    _, _, L_A = make(256, density=1.396)
    assert L_A == pytest.approx(23.0, abs=0.01)


@pytest.mark.parametrize("N", VALID_N)
def test_box_length_matches_mass_density(N: int):
    _, _, L_A = make(N)
    mass_g = N * A_MOLAR_MASS / AVOGADRO
    volume_cm3 = (L_A * 1e-8) ** 3
    assert mass_g / volume_cm3 == pytest.approx(A_DENSITY, rel=1e-12)


def test_reduced_and_angstrom_box_lengths_are_consistent():
    _, L_red, L_A = make(256)
    assert L_red * A_SIGMA == pytest.approx(L_A, rel=1e-12)


@pytest.mark.parametrize("N", VALID_N)
def test_reduced_density_matches_closed_form(N: int):
    _, L_red, _ = make(N)
    rho_star = A_DENSITY * AVOGADRO * (A_SIGMA * 1e-8) ** 3 / A_MOLAR_MASS
    assert N / L_red**3 == pytest.approx(rho_star, rel=1e-12)


def test_doubling_density_shrinks_box_by_cube_root_of_two():
    _, _, L1 = make(256, density=1.0)
    _, _, L2 = make(256, density=2.0)
    assert L1 / L2 == pytest.approx(2 ** (1 / 3), rel=1e-12)


def test_reduced_box_length_scales_inversely_with_sigma():
    _, L1, _ = make(256, sigma=3.0)
    _, L2, _ = make(256, sigma=6.0)
    assert L1 / L2 == pytest.approx(2.0, rel=1e-12)


# ---------- perfect FCC geometry (jiggle = 0) ----------
@pytest.mark.parametrize("N", VALID_N)
def test_perfect_lattice_sites_are_fcc(N: int):
    # In units of a/2, FCC sites are integer triples (i, j, k) with i+j+k even.
    pos, L_red, _ = make(N)
    a = L_red / round((N / 4) ** (1 / 3))
    idx = pos / (a / 2)
    assert np.allclose(idx, np.round(idx), atol=1e-9)
    assert np.all(np.round(idx).sum(axis=1) % 2 == 0)


@pytest.mark.parametrize("N", VALID_N)
def test_perfect_lattice_nearest_neighbour_distance(N: int):
    pos, L_red, _ = make(N)
    a = L_red / round((N / 4) ** (1 / 3))
    d = nn_distances(pos, L_red)
    assert np.allclose(d.min(axis=1), a / np.sqrt(2), rtol=1e-9)


@pytest.mark.parametrize("N", [32, 108, 256])
def test_perfect_lattice_has_12_nearest_neighbours(N: Literal[32, 108, 256]):
    pos, L_red, _ = make(N)
    a = L_red / round((N / 4) ** (1 / 3))
    counts = (np.isclose(nn_distances(pos, L_red), a / np.sqrt(2), rtol=1e-9)).sum(
        axis=1
    )
    assert np.all(counts == 12)


@pytest.mark.parametrize("N", VALID_N)
def test_all_sites_are_unique(N: int):
    pos, _, _ = make(N)
    assert len(np.unique(np.round(pos, 9), axis=0)) == N


def test_perfect_lattice_ignores_seed():
    p1, _, _ = make(108, seed=1)
    p2, _, _ = make(108, seed=2)
    p3, _, _ = make(108, seed=None)
    assert np.array_equal(p1, p2)
    assert np.array_equal(p1, p3)


# ---------- jiggle ----------
def test_jiggle_changes_positions():
    perfect, _, _ = make(108)
    jiggled, _, _ = make(108, jiggle=0.02, seed=0)
    assert not np.allclose(perfect, jiggled)


@pytest.mark.parametrize("jiggle", [0.01, 0.02, 0.1])
def test_jiggle_displacement_bounded_by_fraction_of_cell_edge(jiggle: float):
    N = 108
    perfect, L_red, _ = make(N)
    jiggled, _, _ = make(N, jiggle=jiggle, seed=3)
    a = L_red / round((N / 4) ** (1 / 3))
    disp = min_image(jiggled - perfect, L_red)
    assert np.max(np.abs(disp)) <= jiggle * a + 1e-12


def test_jiggle_is_relative_to_cell_edge_not_box_side():
    # For N=256 (n=4), the max shift is jiggle * L / 4, clearly below jiggle * L.
    N, jiggle = 256, 0.02
    perfect, L_red, _ = make(N)
    jiggled, _, _ = make(N, jiggle=jiggle, seed=5)
    disp = min_image(jiggled - perfect, L_red)
    assert np.max(np.abs(disp)) <= jiggle * L_red / 4 + 1e-12


def test_jiggle_is_reproducible_with_same_seed():
    p1, _, _ = make(108, jiggle=0.05, seed=42)
    p2, _, _ = make(108, jiggle=0.05, seed=42)
    assert np.array_equal(p1, p2)


def test_jiggle_differs_with_different_seed():
    p1, _, _ = make(108, jiggle=0.05, seed=1)
    p2, _, _ = make(108, jiggle=0.05, seed=2)
    assert not np.array_equal(p1, p2)


def test_jiggle_does_not_change_box_size():
    _, L1, A1 = make(108)
    _, L2, A2 = make(108, jiggle=0.1, seed=0)
    assert (L1, A1) == (L2, A2)


def test_small_jiggle_creates_no_overlaps():
    pos, L_red, _ = make(256, jiggle=0.02, seed=0)
    assert nn_distances(pos, L_red).min() > 1.0  # well above 1 sigma


# ---------- internal consistency check ----------
def test_density_mismatch_raises_runtime_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(lj_fluid_init, "ANGSTROM3_PER_CM3", 1e23)  # wrong unit factor
    with pytest.raises(RuntimeError, match="Reduced density mismatch"):
        make(32)
