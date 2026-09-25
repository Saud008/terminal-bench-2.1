#[path = "../fcard_lex/parse.rs"]
pub mod fcard_lex;
#[path = "../wmeter_hdr/extract.rs"]
pub mod wmeter_hdr;
#[path = "../tan_pixsky/project.rs"]
pub mod tan_pixsky;
#[path = "../det_rows/stage.rs"]
pub mod det_rows;
#[path = "../gc_match/match_engine.rs"]
pub mod gc_match;
#[path = "../src_flags/mask.rs"]
pub mod src_flags;
#[path = "../rms_atlas/emit.rs"]
pub mod rms_atlas;
#[path = "../plate_decoy/plate.rs"]
pub mod plate_decoy;
#[path = "../model/wcs_types.rs"]
pub mod types;

pub fn header_root() -> String {
    std::env::var("TB3_HEADER_DIR").unwrap_or_else(|_| "/app/fixtures/headers".to_string())
}

pub fn match_arcsec_override() -> Option<f64> {
    std::env::var("TB3_MATCH_ARCSEC")
        .ok()
        .and_then(|v| v.parse().ok())
}
