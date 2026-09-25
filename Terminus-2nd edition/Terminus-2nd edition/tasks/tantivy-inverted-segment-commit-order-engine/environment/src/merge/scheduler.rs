use crate::ingest::remap::merge_posting_maps;
use crate::merge::finalize::count_live_at_finalize;
use crate::schema::norm::merge_field_norms;
use crate::segment::{save_segment, Doc, Segment};
use crate::staging::{load_catalog, save_catalog};
use std::time::{SystemTime, UNIX_EPOCH};

pub fn merge_staging_segments(index: &str) -> Result<String, String> {
    let mut cat = load_catalog()?;
    let state = cat
        .indexes
        .get_mut(index)
        .ok_or_else(|| format!("index {index} missing"))?;
    if state.staging_segment_ids.len() < 2 {
        return Err("need at least two staging segments to merge".into());
    }

    let seg_ids = state.staging_segment_ids.clone();
    let mut segs: Vec<Segment> = Vec::new();
    for id in &seg_ids {
        segs.push(crate::segment::load_segment(index, id)?);
    }

    let merged_id = format!(
        "merged-{}",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| e.to_string())?
            .as_nanos()
    );

    let mut all_docs: Vec<Doc> = Vec::new();
    let mut all_tombstones: Vec<u32> = Vec::new();
    let mut combined: std::collections::BTreeMap<String, Vec<u32>> = std::collections::BTreeMap::new();
    let mut doc_offset = 0u32;

    for seg in &segs {
        for doc in &seg.docs {
            all_docs.push(Doc {
                doc_id: doc_offset + doc.doc_id,
                title: doc.title.clone(),
                body: doc.body.clone(),
            });
        }
        combined = merge_posting_maps(&combined, &seg.postings);
        for t in &seg.tombstones {
            all_tombstones.push(doc_offset + t);
        }
        doc_offset += seg.docs.len() as u32;
    }

    all_tombstones.sort_unstable();
    all_tombstones.dedup();

    let merged = Segment {
        segment_id: merged_id.clone(),
        docs: all_docs,
        postings: combined,
        tombstones: all_tombstones,
        field_norms: merge_field_norms(&segs),
    };
    save_segment(index, &merged)?;

    state.committed_segment_ids.push(merged_id.clone());
    state.reader_registry.push(merged_id.clone());
    for id in &seg_ids {
        state.obsolete_segment_ids.push(id.clone());
    }
    state.staging_segment_ids.clear();
    state.pending_live_docs = count_live_at_finalize(&merged);
    save_catalog(&cat)?;

    Ok(merged_id)
}
