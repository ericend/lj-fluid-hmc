use std::vec;

use crate::interactions::lennard_jones;
/// Calculates the squared distance between two particles in a periodic cubic
/// box, using the minimum image convention, in reduced units of `sigma²`.
///
/// Each component of the separation `Δ = a − b` is wrapped to the nearest
/// periodic image:
///
/// ```text
/// Δ ← Δ − L · round(Δ / L)
/// ```
///
/// so every component lies in `[−L/2, L/2]`. The result is the squared
/// Euclidean norm of the wrapped separation divided by `sigma²`, which is
/// dimensionless:
///
/// ```text
/// r*² = |Δ|² / σ²
/// ```
///
/// Positions may lie outside the box, since wrapping handles any number of
/// box lengths.
///
/// # Arguments
///
/// * `a`, `b` - Particle positions `[x, y, z]`.
/// * `box_len` - Side length of the cubic box, in the same units as the positions.
/// * `sigma` - Lennard-Jones size parameter: the separation at which the pair
///   potential is zero. Must use the same length units as the positions.
///
/// # Panics
///
/// Panics if `box_len` or `sigma` is not positive and finite.
///
/// # Examples
///
/// ```
/// use energy::interatomic_distance_sq;
///
/// // 0.2 apart through the boundary (not 9.8), so |Δ|² = 0.04.
/// // With sigma = 2.0 the reduced value is 0.04 / 4 = 0.01.
/// let r2 = interatomic_distance_sq([0.1, 0.0, 0.0], [9.9, 0.0, 0.0], 10.0, 2.0);
/// assert!((r2 - 0.01).abs() < 1e-12);
/// ```
///
/// ```should_panic
/// use energy::interatomic_distance_sq;
/// interatomic_distance_sq([0.0; 3], [1.0; 3], 0.0, 1.0); // bad box_len
/// ```
///
/// ```should_panic
/// use energy::interatomic_distance_sq;
/// interatomic_distance_sq([0.0; 3], [1.0; 3], 10.0, 0.0); // bad sigma
/// ```
pub fn interatomic_distance_sq(a: [f64; 3], b: [f64; 3], box_len: f64, sigma: f64) -> f64 {
    assert!(
        box_len > 0.0 && box_len.is_finite(),
        "box_len must be positive and finite, got {box_len}"
    );
    assert!(
        sigma > 0.0 && sigma.is_finite(),
        "sigma must be positive and finite, got {sigma}"
    );

    let inv_box = 1.0 / box_len;

    let mut dx = a[0] - b[0];
    let mut dy = a[1] - b[1];
    let mut dz = a[2] - b[2];

    dx -= box_len * (dx * inv_box).round();
    dy -= box_len * (dy * inv_box).round();
    dz -= box_len * (dz * inv_box).round();

    (dx * dx + dy * dy + dz * dz) / (sigma * sigma)
}

pub fn particle_energy(
    positions: &[[f64; 3]],
    box_len: f64,
    sigma: f64,
    cutoff: f64,
) -> Result<Vec<f64>, &'static str> {
    let n = positions.len();
    let mut energies = vec![0.0; n];
    let r_c = if cutoff != 0.0 { cutoff } else { 2.5 * sigma };
    let r_c2 = r_c * r_c;

    for i in 0..n {
        for j in (i + 1)..n {
            let dr = interatomic_distance_sq(positions[i], positions[j], box_len, sigma);
            if dr > r_c2 {
                continue; // Truncation
            }
            let u = lennard_jones(dr)?;
            let half = 0.5 * u;
            energies[i] += half;
            energies[j] += half;
        }
    }
    Ok(energies)
}

/// Return the full system energy by summing over each particles energy calculated using
/// lennard-jones potential in ```particle_energy ```
pub fn system_energy(
    positions: &[[f64; 3]],
    box_len: f64,
    sigma: f64,
) -> Result<f64, &'static str> {
    Ok(particle_energy(positions, box_len, sigma, r_c)?
        .iter()
        .sum())
}

/// -------------Test for interatomic distance func. --------------------
#[cfg(test)]
mod tests {
    use super::*;

    /// Floating-point comparison with an absolute tolerance.
    fn close(a: f64, b: f64) -> bool {
        (a - b).abs() < 1e-12
    }

    // Most tests use sigma = 1.0 so the result is the plain squared distance.

    #[test]
    fn identical_points_have_zero_distance() {
        let p = [1.0, 1.0, 1.0];
        assert_eq!(interatomic_distance_sq(p, p, 1.0, 1.0), 0.0);
    }

    #[test]
    fn no_wrapping_within_half_box() {
        // 3-4-5 triangle: r² = 25
        let r2 = interatomic_distance_sq([0.0; 3], [3.0, 4.0, 0.0], 100.0, 1.0);
        assert!(close(r2, 25.0));
    }

    #[test]
    fn wraps_across_boundary() {
        let r2 = interatomic_distance_sq([0.1, 0.0, 0.0], [9.9, 0.0, 0.0], 10.0, 1.0);
        assert!(close(r2, 0.04)); // not 9.8² = 96.04
    }

    #[test]
    fn wraps_in_every_axis() {
        let r2 = interatomic_distance_sq([0.1; 3], [9.9; 3], 10.0, 1.0);
        assert!(close(r2, 3.0 * 0.2 * 0.2));
    }

    #[test]
    fn handles_positions_outside_the_box() {
        // 25.1 ≡ 5.1 in a box of 10, which is 0.2 from 4.9
        let r2 = interatomic_distance_sq([25.1, 0.0, 0.0], [4.9, 0.0, 0.0], 10.0, 1.0);
        assert!(close(r2, 0.04));
    }

    #[test]
    fn is_symmetric() {
        let a = [0.3, 7.2, 9.9];
        let b = [8.8, 1.1, 0.4];
        assert!(close(
            interatomic_distance_sq(a, b, 10.0, 1.0),
            interatomic_distance_sq(b, a, 10.0, 1.0),
        ));
    }

    #[test]
    fn never_exceeds_half_box_diagonal() {
        // Max minimum-image distance is √3·L/2, so r² = 3·(L/2)² = 75
        let r2 = interatomic_distance_sq([0.0; 3], [5.0; 3], 10.0, 1.0);
        assert!(close(r2, 75.0));
    }

    #[test]
    fn reduced_units_scale_by_sigma_squared() {
        // 3-4-5 triangle with sigma = 2: 25 / 4 = 6.25 (dividing by sigma gives 12.5)
        let r2 = interatomic_distance_sq([0.0; 3], [3.0, 4.0, 0.0], 100.0, 2.0);
        assert!(close(r2, 6.25));
    }

    #[test]
    #[should_panic(expected = "box_len must be positive")]
    fn zero_box_panics() {
        interatomic_distance_sq([0.0; 3], [1.0; 3], 0.0, 1.0);
    }

    #[test]
    #[should_panic(expected = "box_len must be positive")]
    fn nan_box_panics() {
        interatomic_distance_sq([0.0; 3], [1.0; 3], f64::NAN, 1.0);
    }

    #[test]
    #[should_panic(expected = "sigma must be positive")]
    fn zero_sigma_panics() {
        interatomic_distance_sq([0.0; 3], [1.0; 3], 10.0, 0.0);
    }
}
