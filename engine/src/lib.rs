//! PyO3 module bindings for the Lennard-Jones simulation physics kernel.

pub mod energy;
pub mod integrator;
pub mod interactions;
pub mod pbc;
use pyo3::prelude::*;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Periodic boundary conditions
    m.add_function(wrap_pyfunction!(pbc::minimum_image, m)?)?;
    m.add_function(wrap_pyfunction!(pbc::wrap_pbc, m)?)?;

    // Math & numerical utilities
    m.add_function(wrap_pyfunction!(integrator::velocity_backwards, m)?)?;

    Ok(())
}
