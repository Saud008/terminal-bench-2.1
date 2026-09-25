pub mod attr;
pub mod bind;
pub mod decode;
pub mod export;
pub mod export_nh;
pub mod model;
pub mod route_table_digest;
pub mod snapshot_guard;

use std::path::Path;

use anyhow::Result;

pub fn run_decode(dump: &Path, output: &Path) -> Result<i32> {
    let data = std::fs::read(dump)?;
    let (seed, raw) = decode::parse_dump(&data)?;
    let routes = bind::bind_routes(&seed, raw);
    let bind_snapshot = bind::write_bind_snapshot(dump, &seed, routes)?;
    snapshot_guard::validate_bind_snapshot_file(&bind_snapshot)?;
    let nh_snapshot = export_nh::write_nh_snapshot(&bind_snapshot)?;
    export::write_export_from_nh_snapshot(output, &nh_snapshot)?;
    Ok(0)
}
