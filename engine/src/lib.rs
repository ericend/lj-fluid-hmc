//! PyO3 module bindings for the Lennard-Jones simulation physics kernel.

pub mod integrator;
pub mod interactions;
pub mod lattice;
pub mod pbc;
use pyo3::prelude::*;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Lattice
    m.add_function(wrap_pyfunction!(lattice::init_fcc_py, m)?)?;

    // Potential and kinetic energies
    m.add_function(wrap_pyfunction!(interactions::lennard_jones, m)?)?;
    m.add_function(wrap_pyfunction!(interactions::kinetic_energy, m)?)?;

    // Periodic boundary conditions
    m.add_function(wrap_pyfunction!(pbc::minimum_image, m)?)?;
    m.add_function(wrap_pyfunction!(pbc::wrap_pbc, m)?)?;

    // Math & numerical utilities
    m.add_function(wrap_pyfunction!(integrator::velocity_backwards, m)?)?;

    Ok(())
}
