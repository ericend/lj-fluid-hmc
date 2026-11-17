//! Potential energy and kinetic energy calculations.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Compute the Lennard-Jones pair potential for a displacement vector.
///
/// Evaluates:
///     U(r) = 4 * epsilon * ((sigma / r)^12 - (sigma / r)^6)
/// where `r` is the Euclidean norm of the displacement vector.
#[pyfunction]
#[pyo3(signature = (r, epsilon, sigma))]
pub fn lennard_jones(r: Vec<f64>, epsilon: f64, sigma: f64) -> PyResult<f64> {
    if epsilon <= 0.0 {
        return Err(PyValueError::new_err("Epsilon must be positive"));
    }
    if sigma <= 0.0 {
        return Err(PyValueError::new_err("Sigma must be positive"));
    }

    let r2: f64 = r.iter().map(|x| x * x).sum();
    if r2 == 0.0 {
        return Err(PyValueError::new_err(
            "Lennard-Jones potential is undefined at zero separation",
        ));
    }

    let sigma_over_r_sq = (sigma * sigma) / r2;
    let sigma_over_r_6 = sigma_over_r_sq * sigma_over_r_sq * sigma_over_r_sq;
    let sigma_over_r_12 = sigma_over_r_6 * sigma_over_r_6;

    Ok(4.0 * epsilon * (sigma_over_r_12 - sigma_over_r_6))
}

/// Calculate the kinetic energy of a particle with velocity vector `v` and mass `m`.
#[pyfunction]
#[pyo3(signature = (v, m))]
pub fn kinetic_energy(v: [f64; 3], m: f64) -> PyResult<f64> {
    if m <= 0.0 {
        return Err(PyValueError::new_err("The mass must be positive"));
    }
    let v_sq = v[0].mul_add(v[0], v[1].mul_add(v[1], v[2] * v[2]));
    Ok(0.5 * m * v_sq)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lj_zero_at_sigma() {
        let val = lennard_jones(vec![1.5, 0.0, 0.0], 1.0, 1.5).unwrap();
        assert!((val - 0.0).abs() < 1e-12);
    }

    #[test]
    fn test_lj_minimum_is_minus_epsilon() {
        let r_min = 2.0f64.powf(1.0 / 6.0) * 1.5;
        let val = lennard_jones(vec![r_min, 0.0, 0.0], 2.0, 1.5).unwrap();
        assert!((val - (-2.0)).abs() < 1e-12);
    }

    #[test]
    fn test_kinetic_energy() {
        let ke = kinetic_energy([1.0, 2.0, 2.0], 2.0).unwrap();
        // 0.5 * 2.0 * (1 + 4 + 4) = 9.0
        assert!((ke - 9.0).abs() < 1e-12);
    }
}
