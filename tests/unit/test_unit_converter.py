import math

from modules.parameters import ARGON as u
from modules.parameters import celsius_to_kelvin


def test_tau_argon() -> None:
    assert math.isclose(u.tau, 2.15e-12, rel_tol=0.02)


def test_round_trips() -> None:
    assert math.isclose(u.temp_si(u.temp_red(300.0)), 300.0)
    assert math.isclose(u.density_si(u.density_red(1374.0)), 1374.0)
    assert math.isclose(u.pressure_si(u.pressure_red(1e5)), 1e5)


def test_celsius() -> None:
    assert celsius_to_kelvin(0.0) == 273.15
