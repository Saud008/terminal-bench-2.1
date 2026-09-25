use std::path::Path;

use crate::export::build_export_doc;
use crate::ledger;
use crate::parser::parse_file;
use crate::publish::load_staged_export_input;
use crate::ruby::apply_ruby_shifts;
use crate::ssrrn_staging::{self, write_snapshot};
use crate::ssrrn_timeline::resolve_overlaps;
use crate::types::{ExportDoc, seed_offset_ms};

pub fn run_normalize(path: &Path, seed: &str, fixture: &str) -> ExportDoc {
    let snapshot_path = run_stage(path, seed, fixture);
    run_export(&snapshot_path, path, seed)
}

fn run_stage(path: &Path, seed: &str, fixture: &str) -> std::path::PathBuf {
    let parsed = parse_file(path);
    let parsed_count = parsed.len() as u32;
    let offset = seed_offset_ms(seed);

    let offset_cues: Vec<_> = parsed
        .into_iter()
        .map(|mut cue| {
            cue.start_ms = cue.start_ms.saturating_add(offset);
            cue.end_ms = cue.end_ms.saturating_add(offset);
            cue
        })
        .collect();

    let (ruby_first, ruby_shifts) = apply_ruby_shifts(offset_cues);
    let overlap_input: Vec<_> = ruby_first
        .into_iter()
        .map(|cue| crate::types::ParsedCue {
            source_index: cue.source_index,
            start_ms: cue.start_ms,
            end_ms: cue.end_ms,
            lines: cue.text.lines().map(str::to_string).collect(),
            has_an8: !cue.ruby_segments.is_empty(),
        })
        .collect();
    let (overlap_resolved, overlap_trims) = resolve_overlaps(overlap_input);
    let ruby_applied: Vec<_> = overlap_resolved
        .into_iter()
        .map(|cue| crate::ruby::RubyCue {
            source_index: cue.source_index,
            start_ms: cue.start_ms,
            end_ms: cue.end_ms,
            text: cue.lines.join("\n"),
            ruby_segments: Vec::new(),
            rolled_up: false,
        })
        .collect();

    let digest = ssrrn_staging::input_digest(path);
    let export_seq = ledger::planned_export_seq(fixture, seed);
    let snapshot_path = write_snapshot(
        path,
        fixture,
        seed,
        offset,
        parsed_count,
        overlap_trims,
        ruby_shifts,
        ruby_applied,
    );
    ledger::write(&snapshot_path, fixture, seed, &digest, export_seq);
    snapshot_path
}

fn run_export(snapshot_path: &Path, input_path: &Path, seed: &str) -> ExportDoc {
    let snapshot = ssrrn_staging::read_snapshot(snapshot_path);
    let export_seq = ledger::planned_export_seq(&snapshot.fixture, seed);
    let staged = load_staged_export_input(snapshot_path, input_path, seed, export_seq);
    build_export_doc(staged)
}
