use std::path::Path;

use crate::checkpoint::{append_checkpoint, checkpoint_seen_keys, load_checkpoint};
use crate::dedup::dedup_frames;
use crate::error::Result;
use crate::fact_diff::compute_diff_rows;
use crate::model::ExportDoc;
use crate::parse::extract_frames;
use crate::publish::publish_from_snapshot;
use crate::snapshot::write_decode_snapshot;
use crate::seed::permute_frames;
use crate::session::SessionFilter;
use crate::validate::validate_frames;

pub struct DecodeOptions<'a> {
    pub seed: &'a str,
    pub checkpoint: Option<&'a Path>,
    pub resume: bool,
}

pub fn decode_stream(bytes: &[u8], opts: &DecodeOptions<'_>) -> Result<ExportDoc> {
    let mut frames = extract_frames(bytes)?;
    permute_frames(&mut frames, opts.seed);
    let validated = validate_frames(frames)?;

    let checkpoint_frames = if opts.resume {
        match opts.checkpoint {
            Some(path) => load_checkpoint(path, opts.seed)?,
            None => Vec::new(),
        }
    } else {
        Vec::new()
    };
    let checkpoint_count = checkpoint_frames.len() as u32;

    let seen = match opts.checkpoint {
        Some(path) if opts.resume => checkpoint_seen_keys(path, opts.seed)?,
        _ => std::collections::HashSet::new(),
    };

    let mut session = SessionFilter::new();
    if opts.resume {
        session.seed_from_checkpoint(&checkpoint_frames);
    }
    let (sessioned, stale_dropped) = session.filter(validated)?;

    let (deduped_new, dup_count) = dedup_frames(sessioned, &seen)?;

    if let Some(path) = opts.checkpoint {
        append_checkpoint(path, opts.seed, &deduped_new)?;
    }

    let diff_rows = if opts.resume {
        compute_diff_rows(&checkpoint_frames, &deduped_new)?
    } else {
        Vec::new()
    };

    // Broken: new rows before checkpoint rows (must fail triple-pass order tests).
    let mut merged = deduped_new;
    merged.extend(checkpoint_frames);

    write_decode_snapshot(
        &merged,
        opts.seed,
        checkpoint_count,
        dup_count,
        stale_dropped,
        &diff_rows,
    )?;
    publish_from_snapshot()
}
