//! Mathematical and numerical differentiation helper functions.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Estimate velocity from backward difference: (r_curr - r_prev) / dt.
#[pyfunction]
#[pyo3(signature = (r_prev, r_curr, dt))]
pub fn velocity_backwards(r_prev: [f64; 3], r_curr: [f64; 3], dt: f64) -> PyResult<[f64; 3]> {
    if dt <= 0.0 {
        return Err(PyValueError::new_err("Timestep dt must be positive"));
    }
    Ok([
        (r_curr[0] - r_prev[0]) / dt,
        (r_curr[1] - r_prev[1]) / dt,
        (r_curr[2] - r_prev[2]) / dt,
    ])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_velocity_backwards() {
        let r_prev = [1.0, 2.0, 3.0];
        let r_curr = [1.5, 2.0, 1.0];
        let dt = 0.5;
        let v = velocity_backwards(r_prev, r_curr, dt).unwrap();
        assert!((v[0] - 1.0).abs() < 1e-12);
        assert!((v[1] - 0.0).abs() < 1e-12);
        assert!((v[2] - (-4.0)).abs() < 1e-12);
    }
}
