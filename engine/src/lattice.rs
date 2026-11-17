use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::{pyfunction, PyErr};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use std::fmt;

/// Particles per mol.
pub const AVOGADRO: f64 = 6.022_140_76e23;
/// 1 cm = 1e8 Å, so 1 cm³ = (1e8)³ = 1e24 Å³.
pub const ANGSTROM3_PER_CM3: f64 = 1e24;

#[derive(Debug, Clone, PartialEq)]
pub enum InitError {
    /// An input was non-positive, or `jiggle` was negative or not finite.
    InvalidInput(String),
    /// `N` is not of the form `4 * n^3`.
    InvalidCount(usize),
    /// Final reduced density disagrees with the closed-form value.
    DensityMismatch,
}

impl fmt::Display for InitError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            InitError::InvalidInput(s) => write!(f, "{s}"),
            InitError::InvalidCount(n) => write!(
                f,
                "N={n} is not a valid FCC count (4*n^3): 32, 108, 256, 500, 864, ..."
            ),
            InitError::DensityMismatch => {
                write!(f, "Reduced density mismatch; check inputs/units.")
            }
        }
    }
}

impl std::error::Error for InitError {}

impl From<InitError> for PyErr {
    fn from(err: InitError) -> Self {
        match err {
            InitError::InvalidInput(_) | InitError::InvalidCount(_) => {
                PyValueError::new_err(err.to_string())
            }
            InitError::DensityMismatch => PyRuntimeError::new_err(err.to_string()),
        }
    }
}

/// Initialize a Lennard-Jones fluid on an FCC lattice from physical density.
///
/// `n_particles` particles are placed on a face-centred-cubic lattice that
/// fills a cubic periodic box whose volume reproduces the requested mass
/// density. An optional random displacement breaks the lattice symmetry.
/// With `jiggle = 0.0` the lattice is perfect.
///
/// # Arguments
///
/// * `n_particles` - Must equal `4 * n^3` for integer `n` (32, 108, 256,
///   500, 864, ...).
/// * `density` - Target mass density in g/cm³ (e.g. 1.374 for liquid argon).
/// * `molar_mass` - Molar mass in g/mol (e.g. 39.948 for argon).
/// * `sigma` - Lennard-Jones sigma in Å (e.g. 3.405 for argon). Returned
///   positions are in multiples of this length.
/// * `jiggle` - Maximum random displacement per coordinate, as a fraction of
///   the cubic cell edge `a = L / n`. Each coordinate is shifted by an
///   independent uniform number in `[-jiggle * a, +jiggle * a]`.
/// * `rng` - Seedable RNG used for the jiggle. Pass a `ChaCha8Rng` created
///   with `seed_from_u64` for reproducibility. Has no effect if
///   `jiggle == 0`.
///
/// # Returns
///
/// `(positions, box_length_reduced, box_length_angstrom)`, where `positions`
/// are in reduced units, wrapped into `[0, box_length_reduced)`.
///
/// # Errors
///
/// * [`InitError::InvalidInput`] if any physical input is non-positive.
/// * [`InitError::InvalidCount`] if `n_particles` is not `4 * n^3`.
/// * [`InitError::DensityMismatch`] if the final reduced density does not
///   match the closed-form value (sanity check against unit mistakes).
///
/// # Notes
///
/// The reduced number density is
/// `rho* = N * sigma^3 / V = density * N_A * sigma^3 / molar_mass`.
/// The nearest-neighbour distance is `a / sqrt(2)` (12 neighbours per atom).
/// A perfect lattice has zero net force on every atom by symmetry.
///
/// # Example
///
/// ```ignore
/// use rand_chacha::ChaCha8Rng;
/// use rand::SeedableRng;
///
/// let mut rng = ChaCha8Rng::seed_from_u64(42);
/// let (pos, l_red, l_a) = init_fcc(256, 1.396, 39.948, 3.405, 0.0, &mut rng).unwrap();
/// assert_eq!(pos.len(), 256);
/// assert_eq!((l_a * 10.0).round() / 10.0, 23.0);
/// ```
#[allow(clippy::neg_cmp_op_on_partial_ord)]
pub fn init_fcc(
    n_particles: usize,
    density: f64,
    molar_mass: f64,
    sigma: f64,
    jiggle: f64,
    rng: &mut ChaCha8Rng,
) -> Result<(Vec<[f64; 3]>, f64, f64), InitError> {
    // `!(x > 0.0)` also rejects NaN.
    if n_particles == 0 || !(density > 0.0) || !(molar_mass > 0.0) || !(sigma > 0.0) {
        return Err(InitError::InvalidInput(
            "N, density, molar_mass and sigma must be positive.".into(),
        ));
    }
    if !jiggle.is_finite() || jiggle < 0.0 {
        return Err(InitError::InvalidInput(
            "jiggle must be finite and non-negative.".into(),
        ));
    }

    // N = 4 * n^3  ->  n = (N/4)^(1/3). round() absorbs floating-point error;
    // the integer check below verifies the result is exact.
    let n_cells = ((n_particles as f64 / 4.0).powf(1.0 / 3.0)).round() as usize;
    if 4 * n_cells.pow(3) != n_particles {
        return Err(InitError::InvalidCount(n_particles));
    }

    // Box size from mass density: V = mass / density, L = V^(1/3).
    let volume_a3 = (n_particles as f64 / AVOGADRO) * molar_mass / density * ANGSTROM3_PER_CM3;
    let box_length_angstrom = volume_a3.powf(1.0 / 3.0);
    let box_length_reduced = box_length_angstrom / sigma;
    let a = box_length_reduced / n_cells as f64; // cubic cell edge in sigma

    // 4 atoms of one cubic FCC cell (fractional coordinates).
    const BASIS: [[f64; 3]; 4] = [
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.0],
        [0.5, 0.0, 0.5],
        [0.0, 0.5, 0.5],
    ];

    let mut positions: Vec<[f64; 3]> = Vec::with_capacity(n_particles);
    for i in 0..n_cells {
        for j in 0..n_cells {
            for k in 0..n_cells {
                for b in &BASIS {
                    positions.push([
                        (i as f64 + b[0]) * a,
                        (j as f64 + b[1]) * a,
                        (k as f64 + b[2]) * a,
                    ]);
                }
            }
        }
    }

    // Symmetry-breaking displacement (skipped for a perfect lattice, since
    // an empty range would panic in `random_range`).
    let amp = jiggle * a;
    if amp > 0.0 {
        for p in positions.iter_mut() {
            for x in p.iter_mut() {
                *x += rng.random_range(-amp..amp);
            }
        }
    }

    // Periodic wrap: displaced atoms re-enter on the opposite face.
    for p in positions.iter_mut() {
        for x in p.iter_mut() {
            *x = x.rem_euclid(box_length_reduced);
        }
    }

    // Sanity check (sigma * 1e-8 converts Å to cm), using NumPy's default
    // isclose tolerances: rtol = 1e-5, atol = 1e-8.
    let rho_star = density * AVOGADRO * (sigma * 1e-8).powi(3) / molar_mass;
    let rho_actual = n_particles as f64 / box_length_reduced.powi(3);
    if (rho_actual - rho_star).abs() > 1e-8 + 1e-5 * rho_star.abs() {
        return Err(InitError::DensityMismatch);
    }

    Ok((positions, box_length_reduced, box_length_angstrom))
}

/// Python-facing wrapper exposed as `init_fcc` in the module.
#[pyfunction(name = "init_fcc")]
#[pyo3(signature = (n_particles, density, molar_mass, sigma, jiggle = 0.0, seed = None))]
pub fn init_fcc_py(
    n_particles: usize,
    density: f64,
    molar_mass: f64,
    sigma: f64,
    jiggle: f64,
    seed: Option<u64>,
) -> Result<(Vec<[f64; 3]>, f64, f64), InitError> {
    let mut rng = match seed {
        Some(s) => ChaCha8Rng::seed_from_u64(s),
        None => ChaCha8Rng::from_os_rng(),
    };
    init_fcc(n_particles, density, molar_mass, sigma, jiggle, &mut rng)
}
