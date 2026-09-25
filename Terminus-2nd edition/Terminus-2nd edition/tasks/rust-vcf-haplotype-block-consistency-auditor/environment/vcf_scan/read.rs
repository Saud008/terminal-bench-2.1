use crate::allele_normalize;
use crate::manifest_lineage;
use crate::missing_mask;
use crate::phase_parse;
use crate::types::{Manifest, ParsedGenotype, VariantRecord};
use std::fs;
use std::path::Path;

pub fn load_manifest(path: &Path) -> Result<Manifest, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn parse_vcf(path: &Path, manifest: &Manifest) -> Result<Vec<VariantRecord>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let sample_ids = manifest_lineage::ordered_sample_ids(manifest);
    let mut variants = Vec::new();
    for line in raw.lines() {
        if line.starts_with('#') {
            continue;
        }
        let cols: Vec<&str> = line.split('\t').collect();
        if cols.len() < 10 {
            continue;
        }
        let chrom = cols[0].to_string();
        let pos: u32 = cols[1].parse().map_err(|_| "bad pos".to_string())?;
        let ref_allele = cols[3].to_string();
        let alt_alleles = allele_normalize::normalize_alt_field(cols[4]);
        let fmt_parts: Vec<&str> = cols[8].split(':').collect();
        let gt_idx = fmt_parts.iter().position(|&p| p == "GT").unwrap_or(0);
        let ps_idx = fmt_parts.iter().position(|&p| p == "PS");
        let mut genotypes = Vec::new();
        for (i, sample_id) in sample_ids.iter().enumerate() {
            let cell = cols[9 + i];
            let fields: Vec<&str> = cell.split(':').collect();
            let gt_raw = fields.get(gt_idx).copied().unwrap_or("./.").to_string();
            let ps_tag = ps_idx
                .and_then(|idx| fields.get(idx))
                .map(|s| s.to_string())
                .unwrap_or_default();
            genotypes.push(ParsedGenotype {
                sample_id: sample_id.clone(),
                gt_raw: gt_raw.clone(),
                phased: phase_parse::is_phased(&gt_raw),
                missing: missing_mask::is_missing(&gt_raw),
                alleles: phase_parse::parse_alleles(&gt_raw),
                ps_tag,
            });
        }
        variants.push(VariantRecord {
            chrom,
            pos,
            ref_allele,
            alt_alleles,
            genotypes,
        });
    }
    Ok(variants)
}
