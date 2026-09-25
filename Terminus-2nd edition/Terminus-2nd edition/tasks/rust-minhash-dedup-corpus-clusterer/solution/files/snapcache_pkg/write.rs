use crate::hash_vector;
use crate::shingle_window;
use crate::token_punct;
use crate::token_unicode;
use crate::types::{Config, SketchDoc, SketchIndex};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Path, PathBuf};

pub fn config_fingerprint(cfg: &Config) -> String {
    let body = format!("{}:{}:{}", cfg.shingle_k, cfg.num_hashes, cfg.base_seed);
    hex::encode(Sha256::digest(body.as_bytes()))[..16].to_string()
}

pub fn scan_corpus(
    cfg: &Config,
    corpus_dir: &Path,
    run_id: &str,
    profile: &str,
    salt: &str,
) -> Result<PathBuf, String> {
    let docs = crate::corpus_load::load_corpus_dir(corpus_dir)?;
    let mut sketch_docs = Vec::new();
    for doc in &docs {
        let norm = token_unicode::normalize_unicode(&doc.text);
        let tokens = token_punct::normalize_tokens(&norm);
        let shingles = shingle_window::word_shingles(&tokens, cfg.shingle_k);
        let sig = hash_vector::minhash_signature(&shingles, cfg.base_seed, cfg.num_hashes, salt);
        sketch_docs.push(SketchDoc {
            doc_id: doc.doc_id.clone(),
            source_path: format!("{}/docs.jsonl", corpus_dir.display()),
            token_count: tokens.len() as u32,
            shingle_count: shingles.len() as u32,
            signature: sig,
        });
    }
    sketch_docs.sort_by(|a, b| a.doc_id.cmp(&b.doc_id));

    let index_path = PathBuf::from(&cfg.sketch_index_dir).join(format!("{run_id}.json"));
    let prev_gen = if index_path.exists() {
        let prev: SketchIndex =
            serde_json::from_str(&fs::read_to_string(&index_path).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
        prev.scan_generation
    } else {
        0
    };

    let index = SketchIndex {
        run_id: run_id.to_string(),
        profile: profile.to_string(),
        scan_generation: prev_gen + 1,
        config_fingerprint: config_fingerprint(cfg),
        shingle_k: cfg.shingle_k as u32,
        num_hashes: cfg.num_hashes as u32,
        base_seed: cfg.base_seed,
        documents: sketch_docs,
    };
    fs::create_dir_all(&cfg.sketch_index_dir).map_err(|e| e.to_string())?;
    fs::write(
        &index_path,
        serde_json::to_string_pretty(&index).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    Ok(index_path)
}
