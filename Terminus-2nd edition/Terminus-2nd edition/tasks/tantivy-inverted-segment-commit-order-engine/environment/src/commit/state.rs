use crate::commit::wal::run_wal_barrier;
use crate::segment::{load_segment, live_doc_count, posting_checksum};
use crate::staging::{
    dangling_readers, load_catalog, save_catalog, write_snapshot, IndexState,
};

pub fn commit_index(index: &str) -> Result<(), String> {
    let mut cat = load_catalog()?;
    let state = cat
        .indexes
        .get_mut(index)
        .ok_or_else(|| format!("index {index} missing"))?;

    if state.committed_segment_ids.is_empty() {
        return Err("nothing to commit".into());
    }

    let live = if state.pending_live_docs > 0 {
        state.pending_live_docs
    } else {
        sum_live_docs(index, state)?
    };

    run_wal_barrier(index, live)?;

    state.committed_live_docs = live;
    let dangling = dangling_readers(state);
    let checksum = combined_posting_checksum(index, state)?;
    write_snapshot(
        index,
        live,
        state.committed_segment_ids.len() as u32,
        checksum,
        dangling,
    )?;
    save_catalog(&cat)
}

fn sum_live_docs(index: &str, state: &IndexState) -> Result<u32, String> {
    let mut total = 0u32;
    for id in &state.committed_segment_ids {
        let seg = load_segment(index, id)?;
        total += live_doc_count(&seg);
    }
    Ok(total)
}

fn combined_posting_checksum(index: &str, state: &IndexState) -> Result<u64, String> {
    let mut acc = 0u64;
    for id in &state.committed_segment_ids {
        let seg = load_segment(index, id)?;
        acc ^= posting_checksum(&seg);
    }
    Ok(acc)
}
