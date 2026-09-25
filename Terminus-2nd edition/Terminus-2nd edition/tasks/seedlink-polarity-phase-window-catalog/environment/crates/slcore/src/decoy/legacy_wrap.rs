/// Legacy polarity merge helper — not used by export hot path.
pub fn merge_polarity_hint(body: i8, sheet: i8) -> i8 {
    if body == sheet {
        body
    } else {
        0
    }
}
