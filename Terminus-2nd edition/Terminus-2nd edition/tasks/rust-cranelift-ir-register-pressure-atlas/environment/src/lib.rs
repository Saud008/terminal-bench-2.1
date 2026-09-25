#[path = "../protocol/fluence_models.rs"]
mod fluence_models;
#[path = "../campaign_io/load.rs"]
mod campaign_io;
#[path = "../residual_kernel/subtract.rs"]
mod residual_kernel;
#[path = "../quantize/micron_ev.rs"]
mod quantize;
#[path = "../energy_order/sort.rs"]
mod energy_order;
#[path = "../coincidence_veto/apply.rs"]
mod coincidence_veto;
#[path = "../occupancy_scan/peak.rs"]
mod occupancy_scan;
#[path = "../fluence_ledger/accrue.rs"]
mod fluence_ledger;
#[path = "../closure_rank/order.rs"]
mod closure_rank;
#[path = "../digest_line/seal.rs"]
mod digest_line;
#[path = "../closure_emit/atlas.rs"]
mod closure_emit;

pub use campaign_io::*;
pub use closure_emit::*;
pub use closure_rank::*;
pub use coincidence_veto::*;
pub use digest_line::*;
pub use energy_order::*;
pub use fluence_ledger::*;
pub use fluence_models::*;
pub use occupancy_scan::*;
pub use quantize::*;
pub use residual_kernel::*;

use std::env;
use std::fs;
use std::path::Path;

/// Round-half-away-from-zero at six decimal places; guards float noise identically across
/// accrue-residuals and the independent Python reference math.
pub fn round6(x: f64) -> f64 {
    let scaled = x * 1_000_000.0;
    let rounded = if scaled >= 0.0 {
        (scaled + 0.5).floor()
    } else {
        (scaled - 0.5).ceil()
    };
    rounded / 1_000_000.0
}

pub fn load_config() -> Config {
    let raw = fs::read_to_string("/app/config/fluxpress.json").expect("config");
    let mut cfg: Config = serde_json::from_str(&raw).expect("config json");
    if let Ok(v) = env::var("TB3_MICRON_EV_SCALE") {
        if let Ok(n) = v.parse::<i64>() {
            if n > 0 {
                cfg.micron_ev_scale = n;
            }
        }
    }
    cfg
}

pub fn accrue_residuals(campaign_id: &str, bundle_name: &str) -> Result<(), String> {
    let cfg = load_config();
    let scale = cfg.micron_ev_scale;
    let bundle_path = Path::new(&cfg.bundle_dir).join(format!("{bundle_name}.json"));
    let bundle = load_bundle(&bundle_path)?;

    let mut channels: Vec<FluenceChannel> = Vec::new();
    for ch in &bundle.channels {
        let energy_q = round6(quantize(ch.energy_kev, scale));
        let width_q = round6(quantize(ch.width_kev, scale));
        let vetoed = is_vetoed(&ch.channel_id, energy_q, &bundle.veto_windows, scale);
        let residual = if vetoed {
            0.0
        } else {
            residual_counts(ch.measured_counts, ch.energy_kev, &bundle.background_anchors)
        };
        channels.push(FluenceChannel {
            channel_id: ch.channel_id.clone(),
            energy_q,
            residual_counts: residual,
            width_q,
            vetoed,
        });
    }
    sort_channels(&mut channels);

    let epoch = next_epoch(&cfg.ledger_dir, campaign_id);
    let art = FluenceLedger {
        accrual_epoch: epoch,
        campaign_id: campaign_id.to_string(),
        bundle: bundle_name.to_string(),
        micron_ev_scale: scale,
        aperture_budget: bundle.aperture_budget,
        dwell_width_kev: bundle.dwell_width_kev,
        channels,
    };
    write_ledger(&cfg.ledger_dir, &art)?;
    Ok(())
}

pub fn emit_occupancy(campaign_id: &str, output: &Path) -> Result<(), String> {
    let cfg = load_config();
    let art = read_ledger(&cfg.ledger_dir, campaign_id)?;

    let mut aperture_delta = 0i64;
    if let Ok(v) = env::var("TB3_APERTURE_DELTA") {
        if let Ok(n) = v.parse::<i64>() {
            aperture_delta = n;
        }
    }
    let effective_aperture = (art.aperture_budget + aperture_delta).max(1);

    let occ = scan_occupancy(&art.channels);
    let spill_risk = (occ.max_occupancy as i64) > effective_aperture;

    let channel_order: Vec<String> = art
        .channels
        .iter()
        .filter(|c| !c.vetoed)
        .map(|c| c.channel_id.clone())
        .collect();

    let rows = rank_channels(&art.channels);

    let mut atlas = build_atlas(
        campaign_id,
        effective_aperture,
        channel_order,
        occ.max_occupancy,
        occ.peak_channel_id,
        spill_risk,
        rows,
    );
    atlas.closure_digest = closure_digest(&atlas);

    let parent = output.parent().unwrap_or(Path::new("."));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let body = render_atlas_body(&atlas);
    fs::write(output, body).map_err(|e| e.to_string())?;
    Ok(())
}
