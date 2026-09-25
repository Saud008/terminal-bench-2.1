pub fn quat_normalize(q: [f64; 4]) -> [f64; 4] {
    let mag = (q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]).sqrt();
    if mag == 0.0 {
        return [0.0, 0.0, 0.0, 1.0];
    }
    [q[0] / mag, q[1] / mag, q[2] / mag, q[3] / mag]
}

pub fn quat_slerp(q0: [f64; 4], q1: [f64; 4], t: f64) -> [f64; 4] {
    let a = quat_normalize(q0);
    let mut b = quat_normalize(q1);
    let mut dot = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
    if dot < 0.0 {
        b = [-b[0], -b[1], -b[2], -b[3]];
        dot = -dot;
    }
    if dot > 0.9995 {
        let out = [
            a[0] + t * (b[0] - a[0]),
            a[1] + t * (b[1] - a[1]),
            a[2] + t * (b[2] - a[2]),
            a[3] + t * (b[3] - a[3]),
        ];
        return quat_normalize(out);
    }
    let theta0 = dot.clamp(-1.0, 1.0).acos();
    let sin_theta0 = theta0.sin();
    let theta = theta0 * t;
    let s0 = (theta0 - theta).sin() / sin_theta0;
    let s1 = theta.sin() / sin_theta0;
    quat_normalize([
        s0 * a[0] + s1 * b[0],
        s0 * a[1] + s1 * b[1],
        s0 * a[2] + s1 * b[2],
        s0 * a[3] + s1 * b[3],
    ])
}

pub fn rotate_vec_by_quat(v: [f64; 3], q: [f64; 4]) -> [f64; 3] {
    let [x, y, z] = v;
    let [qx, qy, qz, qw] = quat_normalize(q);
    let ix = qw * x + qy * z - qz * y;
    let iy = qw * y + qz * x - qx * z;
    let iz = qw * z + qx * y - qy * x;
    let iw = -qx * x - qy * y - qz * z;
    [
        ix * qw + iw * -qx + iy * -qz - iz * -qy,
        iy * qw + iw * -qy + iz * -qx - ix * -qz,
        iz * qw + iw * -qz + ix * -qy - iy * -qx,
    ]
}

pub fn lerp3(a: [f64; 3], b: [f64; 3], t: f64) -> [f64; 3] {
    [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    ]
}
