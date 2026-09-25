use crate::types::SampleBarcode;

pub fn match_sample(
    observed: &str,
    samples: &[SampleBarcode],
    budget: u32,
) -> Option<String> {
    let mut best: Option<(String, u32)> = None;
    for sample in samples {
        let dist = hamming_ignore_n(observed, &sample.barcode);
        if dist <= budget {
            match &best {
                None => best = Some((sample.sample_id.clone(), dist)),
                Some((_, bd)) if dist < *bd => best = Some((sample.sample_id.clone(), dist)),
                _ => {}
            }
        }
    }
    best.map(|(id, _)| id)
}

fn hamming_ignore_n(observed: &str, expected: &str) -> u32 {
    if observed.len() != expected.len() {
        return u32::MAX;
    }
    observed
        .chars()
        .zip(expected.chars())
        .filter(|(a, b)| *a != 'N' && *b != 'N' && a != b)
        .count() as u32
}
