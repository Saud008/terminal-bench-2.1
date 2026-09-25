use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Doc {
    pub doc_id: u32,
    pub title: String,
    pub body: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Segment {
    pub segment_id: String,
    pub docs: Vec<Doc>,
    pub postings: BTreeMap<String, Vec<u32>>,
    pub tombstones: Vec<u32>,
    pub field_norms: BTreeMap<String, u32>,
}

pub fn segment_dir(index: &str) -> PathBuf {
    PathBuf::from(format!("/app/data/{index}/segments"))
}

pub fn load_segment(index: &str, seg_id: &str) -> Result<Segment, String> {
    let path = segment_dir(index).join(format!("{seg_id}.json"));
    let raw = fs::read_to_string(&path).map_err(|e| format!("read segment: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse segment: {e}"))
}

pub fn save_segment(index: &str, seg: &Segment) -> Result<(), String> {
    let dir = segment_dir(index);
    fs::create_dir_all(&dir).map_err(|e| format!("mkdir segments: {e}"))?;
    let path = dir.join(format!("{}.json", seg.segment_id));
    fs::write(
        path,
        serde_json::to_string_pretty(seg).map_err(|e| e.to_string())?,
    )
    .map_err(|e| format!("write segment: {e}"))?;
    Ok(())
}

pub fn tokenize_field(field: &str, text: &str) -> Vec<String> {
    let prefix = if field == "body" { "body:" } else { "" };
    text.to_lowercase()
        .split_whitespace()
        .map(|t| t.trim_matches(|c: char| !c.is_alphanumeric()).to_string())
        .filter(|t| !t.is_empty())
        .map(|t| format!("{prefix}{t}"))
        .collect()
}

pub fn build_postings(docs: &[Doc]) -> BTreeMap<String, Vec<u32>> {
    let mut map: BTreeMap<String, Vec<u32>> = BTreeMap::new();
    for doc in docs {
        for term in tokenize_field("title", &doc.title) {
            map.entry(term).or_default().push(doc.doc_id);
        }
        for term in tokenize_field("body", &doc.body) {
            map.entry(term).or_default().push(doc.doc_id);
        }
    }
    for ids in map.values_mut() {
        ids.sort_unstable();
        ids.dedup();
    }
    map
}

pub fn default_field_norms() -> BTreeMap<String, u32> {
    let mut m = BTreeMap::new();
    m.insert("title".to_string(), 1);
    m.insert("body".to_string(), 2);
    m
}

pub fn posting_checksum(seg: &Segment) -> u64 {
    let mut acc: u64 = 0;
    for (term, ids) in &seg.postings {
        acc = acc.wrapping_mul(31).wrapping_add(term.len() as u64);
        for id in ids {
            acc = acc.wrapping_mul(131).wrapping_add(*id as u64);
        }
    }
    acc
}

pub fn live_doc_count(seg: &Segment) -> u32 {
    let dead: HashSet<u32> = seg.tombstones.iter().copied().collect();
    seg.docs.iter().filter(|d| !dead.contains(&d.doc_id)).count() as u32
}

pub fn search_term(seg: &Segment, field: &str, term: &str) -> Vec<u32> {
    let key = if field == "body" {
        format!("body:{}", term.to_lowercase())
    } else {
        term.to_lowercase()
    };
    let dead: HashSet<u32> = seg.tombstones.iter().copied().collect();
    seg.postings
        .get(&key)
        .map(|ids| {
            ids.iter()
                .copied()
                .filter(|id| !dead.contains(id))
                .collect()
        })
        .unwrap_or_default()
}
