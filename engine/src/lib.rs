use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::thread_rng;
use rand_distr::{Distribution, Normal};

const K_B: f64 = 1.380649e-23;

/// ## Compute the Lennard-Jones pair potential for a displacement vector.
///
/// Evaluates `U(R) = 4 * epsilon * ((sigma / R)^12 - (sigma / R)^6)`
/// where `R` is the Euclidean norm of `r`.
///
/// ## Panics
///
/// Panics if the computed squared separation is zero (i.e. `r` is empty
/// or all its components are zero).
///
/// ## Examples
///
/// ```
/// # use engine::lennard_jones;
/// assert_eq!(lennard_jones([1.0, 0.0, 0.0], 1.0, 1.0), 0.0);
/// ```
#[pyfunction]
# [pyo3(signature = (r, epsilon, sigma))]
pub fn lennard_jones(r: Vec<f64>, epsilon: f64, sigma: f64) -> PyResult<f64> {
    let r2: f64 = r.iter().map(|x| x * x).sum();
    if epsilon <= 0.0 {
        return Err(PyValueError::new_err("Epsilon <= 0.0")); // Should these be panic! ?
    }
    if sigma <= 0.0 {
        return Err(PyValueError::new_err("sigma <= 0.0"));
    }
    if r2 == 0.0 {
        return Err(PyValueError::new_err(
            "Lennard-Jones potential is undefined at zero separation",
        ));
    }

    let sigma_over_r_squared = (sigma * sigma) / r2;
    let sigma_over_r_sixth = sigma_over_r_squared * sigma_over_r_squared * sigma_over_r_squared;
    Ok(4.0 * epsilon * (sigma_over_r_sixth * sigma_over_r_sixth - sigma_over_r_sixth))
}

/// Kinetic Energy
/// Calculate the kinetic energy of a particle in 3D-space
/// where `v` is the velocity vector.
/// ## Panics
///
/// Panics if the mass `m` is zero.
///
/// ## Examples
#[pyfunction]
#[pyo3(signature = (v, m))]
pub fn kinetic_energy(v: [f64; 3], m: f64) -> PyResult<f64> {
    if m <= 0.0 {
        return Err(PyValueError::new_err("The mass must be positive"));
    }
    let v_sq = v[0].mul_add(v[0], v[1].mul_add(v[1], v[2] * v[2])); // mul_add reduces to only one roundig error.
    Ok(0.5 * m * v_sq)
}

// Maxwell drawer
// Draws a velocity from the Maxwell-Boltzmann dsitribution for a particle
//
#[pyfunction]
pub fn sample_maxwell_vel(temp: f64, mass: f64) -> f64 {
    let std_dev = (K_B * temp / mass).sqrt();
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(lennard_jones, m)?)?;
    m.add_function(wrap_pyfunction!(kinetic_energy, m)?)?;
    Ok(())
}
