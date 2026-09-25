/// PEP 440 version rank ladder for candidate tie-breaks.
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

fn compare_release(a: &str, b: &str) -> bool {
    let ua = a.split('-').next().unwrap_or(a);
    let ub = b.split('-').next().unwrap_or(b);
    // NOTE: release segment comparison per pep440-version-order.md
    ua > ub
}
