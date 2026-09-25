#[path = "../gt_parser/phase_parse.rs"]
pub mod phase_parse;
#[path = "../gt_parser/missing_mask.rs"]
pub mod missing_mask;
#[path = "../alt_split/normalize.rs"]
pub mod allele_normalize;
#[path = "../phase_wiring/ps_group.rs"]
pub mod ps_group;
#[path = "../phase_wiring/consistency.rs"]
pub mod block_consistency;
#[path = "../cohort_lineage/lineage.rs"]
pub mod manifest_lineage;
#[path = "../sample_matrix/materialize.rs"]
pub mod sample_matrix;
#[path = "../edge_list/wire.rs"]
pub mod edge_wire;
#[path = "../anomaly_score/consistency_emit.rs"]
pub mod anomaly_report;
#[path = "../vcf_scan/read.rs"]
pub mod vcf_read;
#[path = "../decoy_pca/haplotype_heatmap.rs"]
pub mod decoy_heatmap;
#[path = "../model/haplotype_schema.rs"]
pub mod types;

pub fn ps_salt() -> String {
    std::env::var("TB3_PS_SALT").unwrap_or_default()
}

pub fn vcf_fixture_root() -> String {
    std::env::var("TB3_VCF_DIR").unwrap_or_else(|_| "/app/fixtures/vcf".to_string())
}
