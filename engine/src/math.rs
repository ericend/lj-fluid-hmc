// Backward difference method
pub fn velocity_backwards(r_prev: [f64; 3], r_curr: [f64; 3], dt: f64) -> [f64; 3] {
    if dt <= 0.0 {
        return panic!("Negative or zero timestep dt");
    }
}
