pub fn quat_normalize(q: [f64; 4]) -> [f64; 4] {
    let mag = (q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]).sqrt();
    if mag == 0.0 {
        return [0.0, 0.0, 0.0, 1.0];
    }
    [q[0] / mag, q[1] / mag, q[2] / mag, q[3] / mag]
}

pub fn quat_to_euler(q: [f64; 4]) -> [f64; 3] {
    let [x, y, z, w] = quat_normalize(q);
    let sinr_cosp = 2.0 * (w * x + y * z);
    let cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
    let roll = sinr_cosp.atan2(cosr_cosp);
    let sinp = 2.0 * (w * y - z * x);
    let pitch = if sinp.abs() >= 1.0 {
        std::f64::consts::FRAC_PI_2.copysign(sinp)
    } else {
        sinp.asin()
    };
    let siny_cosp = 2.0 * (w * z + x * y);
    let cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
    let yaw = siny_cosp.atan2(cosy_cosp);
    [roll, pitch, yaw]
}

pub fn euler_to_quat(e: [f64; 3]) -> [f64; 4] {
    let (roll, pitch, yaw) = (e[0], e[1], e[2]);
    let cy = (yaw * 0.5).cos();
    let sy = (yaw * 0.5).sin();
    let cp = (pitch * 0.5).cos();
    let sp = (pitch * 0.5).sin();
    let cr = (roll * 0.5).cos();
    let sr = (roll * 0.5).sin();
    [
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    ]
}

pub fn quat_slerp(q0: [f64; 4], q1: [f64; 4], t: f64) -> [f64; 4] {
    let e0 = quat_to_euler(q0);
    let e1 = quat_to_euler(q1);
    let blended = [
        e0[0] + (e1[0] - e0[0]) * t,
        e0[1] + (e1[1] - e0[1]) * t,
        e0[2] + (e1[2] - e0[2]) * t,
    ];
    euler_to_quat(blended)
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
