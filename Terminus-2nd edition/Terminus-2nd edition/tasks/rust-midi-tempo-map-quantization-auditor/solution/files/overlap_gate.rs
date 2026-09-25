use crate::types::NoteEvent;

fn interval_overlap(a0: u64, a1: u64, b0: u64, b1: u64) -> bool {
    a0 < b1 && b0 < a1
}

pub fn overlaps(a: &NoteEvent, b: &NoteEvent) -> bool {
    if a.lane != b.lane {
        return false;
    }
    let a_end = a.tick.saturating_add(a.duration);
    let b_end = b.tick.saturating_add(b.duration);
    interval_overlap(a.tick, a_end, b.tick, b_end)
}

pub fn rejected_ids(notes: &[NoteEvent]) -> std::collections::BTreeSet<String> {
    let mut rejected = std::collections::BTreeSet::new();
    for i in 0..notes.len() {
        for j in (i + 1)..notes.len() {
            if overlaps(&notes[i], &notes[j]) {
                let loser = if notes[j].id > notes[i].id {
                    notes[j].id.clone()
                } else {
                    notes[i].id.clone()
                };
                rejected.insert(loser);
            }
        }
    }
    rejected
}
