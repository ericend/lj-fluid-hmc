//! PyO3 module bindings for the Lennard-Jones simulation physics kernel.

pub mod math;
pub mod pbc;
pub mod potential;

use pyo3::prelude::*;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Potential and kinetic energies
    m.add_function(wrap_pyfunction!(potential::lennard_jones, m)?)?;
    m.add_function(wrap_pyfunction!(potential::kinetic_energy, m)?)?;

    // Periodic boundary conditions
    m.add_function(wrap_pyfunction!(pbc::minimum_image, m)?)?;
    m.add_function(wrap_pyfunction!(pbc::wrap_pbc, m)?)?;

    // Math & numerical utilities
    m.add_function(wrap_pyfunction!(math::velocity_backwards, m)?)?;

    Ok(())
}
