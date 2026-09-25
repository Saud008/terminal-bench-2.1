pub fn cube_distance(q0: i32, r0: i32, q1: i32, r1: i32) -> i32 {
    let dq = (q1 - q0).abs();
    let dr = (r1 - r0).abs();
    dq.max(dr)
}
