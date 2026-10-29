use pyo3::exceptions::PyValueError;
use pyo3::prelude::*; // import

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
#[pyfunction] //
#[pyo3(signature = (r, epsilon, sigma))]
pub fn lennard_jones(r: Vec<f64>, epsilon: f64, sigma: f64) -> PyResult<f64> {
    let r2: f64 = r.iter().map(|x| x * x).sum();
    if epsilon <= 0.0 {
        return Err(PyValueError::new_err("Epsilon <= 0.0"));
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

#[pymodule]
fn engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(lennard_jones, m)?)?;
    Ok(())
}
