//! Potential energy and kinetic energy calculations.

/// Compute the unitless Lennard-Jones pair potential for
/// the square of some interatomic distance r* dr2, i.e dr2 = (r*)^2.
///
/// Evaluates:
///     U(r*) = 4(/r*)^12 - (/r*)^6)
/// where `r*` is the Euclidean norm of the displacement vector in reduced units.
pub fn lennard_jones(dr2: f64) -> Result<f64, &'static str> {
    if dr2 < 0.0 {
        return Err("Lennard-Jones potential is undefined at zero separation");
    }

    let inv_dr2 = 1.0 / dr2;
    let inv_r6 = inv_dr2 * inv_dr2 * inv_dr2;
    let inv_r12 = inv_r6 * inv_r6;

    Ok(4.0 * (inv_r12 - inv_r6))
}

/// Calculate the kinetic energy of a particle with velocity vector `v` and mass `m`.
pub fn kinetic_energy(v: [f64; 3], m: f64) -> Result<f64, &'static str> {
    if m <= 0.0 {
        return Err("The mass must be positive");
    }
    let v_sq = v[0].mul_add(v[0], v[1].mul_add(v[1], v[2] * v[2]));
    Ok(0.5 * m * v_sq)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lennard_jones_floating_point_error() {
        let expected: f64 = -0.890965287583;
        let res = lennard_jones(1.2).expect("r is nonzero");
        assert!((res - expected).abs() < 1e-6);
    }
    #[test]
    fn test_lennard_jones_returns_error_on_zero_r() {
        assert!(lennard_jones(0.0).is_err());
    }

    #[test]
    fn test_kinetic_energy() {
        let ke = kinetic_energy([1.0, 2.0, 2.0], 2.0).unwrap();
        // 0.5 * 2.0 * (1 + 4 + 4) = 9.0
        assert!((ke - 9.0).abs() < 1e-12);
    }
}
