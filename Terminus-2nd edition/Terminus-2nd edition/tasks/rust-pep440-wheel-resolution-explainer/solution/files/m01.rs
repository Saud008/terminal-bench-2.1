pub fn pep440_gt(a: &str, b: &str) -> bool {
    let (ea, ra) = split_epoch(a);
    let (eb, rb) = split_epoch(b);
    if ea != eb {
        return ea > eb;
    }
    compare_release(ra, rb)
}

fn split_epoch(v: &str) -> (u64, &str) {
    if let Some((e, rest)) = v.split_once(':') {
        (e.parse().unwrap_or(0), rest)
    } else {
        (0, v)
    }
}

fn norm_seg(seg: &str) -> (u8, String) {
    if let Some((base, _)) = seg.split_once('~') {
        (0, base.to_string())
    } else {
        (1, seg.to_string())
    }
}

fn compare_release(a: &str, b: &str) -> bool {
    let ua = a.split('-').next().unwrap_or(a).split('+').next().unwrap_or(a);
    let ub = b.split('-').next().unwrap_or(b).split('+').next().unwrap_or(b);
    let pa: Vec<_> = ua.split('.').map(norm_seg).collect();
    let pb: Vec<_> = ub.split('.').map(norm_seg).collect();
    for (xa, xb) in pa.iter().zip(pb.iter()) {
        if xa != xb {
            return xa > xb;
        }
    }
    if pa.len() != pb.len() {
        return pa.len() > pb.len();
    }
    if a.contains(".post") && !b.contains(".post") {
        return a.starts_with(b.split(".post").next().unwrap_or(b));
    }
    a > b
}
