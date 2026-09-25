#[path = "../mbvcm_r01/load.rs"]
pub mod seismo_peak;
#[path = "../mbvcm_r02/attenuate.rs"]
pub mod ppv_field;
#[path = "../mbvcm_r03/apply.rs"]
pub mod gain_curve;
#[path = "../mbvcm_r04/mbvcm_anchor.rs"]
pub mod parcel_mesh;
#[path = "../mbvcm_r05/limit.rs"]
pub mod jurisdiction;
#[path = "../mbvcm_r06/persist.rs"]
pub mod run_buffer;
#[path = "../mbvcm_r07/audit.rs"]
pub mod passport;
#[path = "../mbvcm_r08/publish.rs"]
pub mod atlas_emit;
#[path = "../waveform_decoy/synth.rs"]
pub mod waveform_decoy;
#[path = "../model/blast_vibration_types.rs"]
pub mod types;

pub const DEFAULT_SURVEY_ROOT: &str = "/app/fixtures/surveys";

pub fn survey_root() -> String {
    std::env::var("TB3_FIXTURE_DIR").unwrap_or_else(|_| DEFAULT_SURVEY_ROOT.to_string())
}

pub fn limit_scale() -> f64 {
    std::env::var("TB3_LIMIT_SCALE")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(1.0)
}
