pub fn rotate_left(seq: &str, shift: u32) -> String {
    if seq.is_empty() {
        return seq.to_string();
    }
    let n = (shift as usize) % seq.len();
    format!("{}{}", &seq[n..], &seq[..n])
}

pub fn reverse_complement(seq: &str) -> String {
    seq.chars()
        .rev()
        .map(complement_base)
        .collect()
}

fn complement_base(base: char) -> char {
    match base {
        'A' => 'T',
        'T' => 'A',
        'C' => 'G',
        'G' => 'C',
        'N' => 'N',
        other => other,
    }
}

pub fn canonical_r1(umi: &str, seed_shift: u32) -> String {
    rotate_left(umi, seed_shift)
}

pub fn canonical_r2(umi: &str, seed_shift: u32) -> String {
    let rc = reverse_complement(umi);
    rotate_left(&rc, seed_shift)
}

pub fn pair_canonical(r1: &str, r2: &str) -> String {
    if r1 <= r2 {
        r1.to_string()
    } else {
        r2.to_string()
    }
}

pub fn tb3_seed_shift_bias() -> u32 {
    std::env::var("TB3_UMI_SEED_SHIFT")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(0)
}
