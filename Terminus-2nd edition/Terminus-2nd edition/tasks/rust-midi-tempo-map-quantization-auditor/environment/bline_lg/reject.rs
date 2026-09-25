use crate::types::NoteEvent;

        pub fn overlaps(a: &NoteEvent, b: &NoteEvent) -> bool {
            a.lane == b.lane && a.tick == b.tick
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
