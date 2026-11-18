//! Periodic boundary conditions and minimum image convention.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Apply the minimum image convention to a displacement vector `dr` in a cubic box of size `box_length`.
///
/// **Frenkel & Smit (2002), Understanding Molecular Simulation (2nd ed.):**
/// > *"In order to simulate bulk phases it is essential to choose boundary conditions
///  that mimic the presence of an infinite bulk surrounding our N-particle model system."*
///
///
/// dX = X_i - X_j
/// dY = Y_i - Y_j
/// dZ = Z_i - Z_j
/// # minimum image, per component
/// dX -= box * np.round(dX / box)
/// dY -= box * np.round(dY / box)
/// dZ -= box * np.round(dZ / box)
/// # compute the distance
/// dR = np.sqrt(dX**2 + dY**2 + dZ**2)
///

#[pyfunction]
#[pyo3(signature = (dr, box_length))]
pub fn minimum_image(dr: [f64; 3], box_length: f64) -> PyResult<[f64; 3]> {
    if box_length <= 0.0 {
        return Err(PyValueError::new_err("Box length must be positive"));
    }

    Ok([
        dr[0] - box_length * (dr[0] / box_length).round(),
        dr[1] - box_length * (dr[1] / box_length).round(),
        dr[2] - box_length * (dr[2] / box_length).round(),
    ])
}

/// Wrap a coordinate vector `r` back into the primary cubic simulation cell `[0, box_length)`.
#[pyfunction]
#[pyo3(signature = (r, box_length))]
pub fn wrap_pbc(r: [f64; 3], box_length: f64) -> PyResult<[f64; 3]> {
    if box_length <= 0.0 {
        return Err(PyValueError::new_err("Box length must be positive"));
    }

    Ok([
        r[0].rem_euclid(box_length),
        r[1].rem_euclid(box_length),
        r[2].rem_euclid(box_length),
    ])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_minimum_image_no_wrapping_needed() {
        let dr = [1.0, -1.0, 0.5];
        let res = minimum_image(dr, 10.0).unwrap();
        assert_eq!(res, [1.0, -1.0, 0.5]);
    }

    #[test]
    fn test_minimum_image_wrapping() {
        let dr = [9.0, -9.0, 5.1];
        let res = minimum_image(dr, 10.0).unwrap();
        // 9.0 - 10 = -1.0; -9.0 + 10 = 1.0; 5.1 - 10 = -4.9
        assert!((res[0] - (-1.0)).abs() < 1e-12);
        assert!((res[1] - 1.0).abs() < 1e-12);
        assert!((res[2] - (-4.9)).abs() < 1e-12);
    }

    #[test]
    fn test_wrap_pbc() {
        let r = [11.5, -2.5, 0.0];
        let res = wrap_pbc(r, 10.0).unwrap();
        assert!((res[0] - 1.5).abs() < 1e-12);
        assert!((res[1] - 7.5).abs() < 1e-12);
        assert!((res[2] - 0.0).abs() < 1e-12);
    }
}
