pub mod bind;
pub mod decoy;
pub mod hopf_weave;
pub mod ken_io;
pub mod m2_table;
pub mod models;
pub mod peskin_emit;
pub mod ppi_loader;
pub mod relay_lane;
pub mod ruelle_ratio;
pub mod stamp_z9;

pub use bind::site_manifest;
pub use decoy::doppler_alias;
pub use hopf_weave::weave as azimuth_bridge;
pub use ken_io::latch as tilt_rank;
pub use m2_table::p4s as offset_apply;
pub use peskin_emit::e5r as stitched_report;
pub use ppi_loader::scan_manifest;
pub use relay_lane::n3w as ndjson_writer;
pub use ruelle_ratio::c6f as completeness;
pub use stamp_z9::v7g as gate_filter;

pub const VAR_ROOT: &str = "/app/var";
pub const DEFAULT_FIXTURE_ROOT: &str = "/app/fixtures/bundles";
