"""
Tests for the Rust `engine` extension module.
"""

import pytest

try:
    import engine

    if not hasattr(engine, "lennard_jones"):
        pytest.skip(
            "Rust engine not built yet (run `maturin develop`)", allow_module_level=True
        )
except ImportError:
    pytest.skip(
        "Rust engine not built yet (run `maturin develop`)", allow_module_level=True
    )


def test_potential_is_zero_at_sigma():
    epsilon = 2.0
    sigma = 1.5
    r = [sigma, 0.0, 0.0]

    potential = engine.lennard_jones(r, epsilon, sigma)

    assert potential == pytest.approx(0.0)


def test_potential_minimum_is_negative_epsilon():
    epsilon = 2.0
    sigma = 1.5
    r_min = 2 ** (1 / 6) * sigma
    r = [r_min, 0.0, 0.0]

    potential = engine.lennard_jones(r, epsilon, sigma)

    assert potential == pytest.approx(-epsilon)


def test_potential_is_repulsive_below_sigma():
    epsilon = 1.0
    sigma = 1.5
    r = [1.0, 0.0, 0.0]

    potential = engine.lennard_jones(r, epsilon, sigma)

    assert potential > 0.0


def test_potential_attractive_above_sigma():
    epsilon = 1.0
    sigma = 1.5
    r = [2.0, 0.0, 0.0]

    potential = engine.lennard_jones(r, epsilon, sigma)

    assert potential < 0.0


def test_zero_separation_raises_value_error():
    epsilon = 1.0
    sigma = 1.5
    r = [0.0, 0.0, 0.0]

    with pytest.raises(ValueError):
        engine.lennard_jones(r, epsilon, sigma)


@pytest.mark.parametrize("sigma", [0.0, -0.1, -1.0])
def test_nonpositive_sigma_raises_value_error(sigma):
    with pytest.raises(ValueError):
        engine.lennard_jones(
            [1.0, 0.0, 0.0],
            epsilon=1.0,
            sigma=sigma,
        )
