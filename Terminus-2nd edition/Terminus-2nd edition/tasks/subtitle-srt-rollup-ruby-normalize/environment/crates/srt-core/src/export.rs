use crate::publish::StagedExportInput;
use crate::rollup::apply_rollup;
use crate::types::{EXPORT_FORMAT, ExportCue, ExportDoc, ExportStats};

pub fn build_export_doc(staged: StagedExportInput) -> ExportDoc {
    let (rolled, rollup_removals) = apply_rollup(staged.cues);
    let cues: Vec<ExportCue> = rolled
        .into_iter()
        .enumerate()
        .map(|(idx, cue)| ExportCue {
            index: (idx + 1) as u32,
            source_index: cue.source_index,
            start_ms: cue.start_ms,
            end_ms: cue.end_ms,
            text: cue.text,
            ruby_segments: cue.ruby_segments,
            rolled_up: cue.rolled_up,
        })
        .collect();
    let exported = cues.len() as u32;
    ExportDoc {
        fixture: staged.fixture,
        seed: staged.seed,
        seed_offset_ms: staged.seed_offset_ms,
        format: EXPORT_FORMAT.to_string(),
        cues,
        stats: ExportStats {
            parsed: staged.parsed_count,
            exported,
            overlap_trims: staged.overlap_trims,
            rollup_removals,
            ruby_shifts: staged.ruby_shifts,
        },
    }
}
