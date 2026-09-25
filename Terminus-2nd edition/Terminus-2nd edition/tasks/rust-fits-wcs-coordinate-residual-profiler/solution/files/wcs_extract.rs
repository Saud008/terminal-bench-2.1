use crate::types::WcsCache;
use std::collections::BTreeMap;

fn parse_f64(map: &BTreeMap<String, String>, key: &str) -> Result<f64, String> {
    map.get(key)
        .ok_or_else(|| format!("missing {key}"))
        .and_then(|v| v.parse().map_err(|_| format!("bad float {key}")))
}

pub fn extract_wcs(run_id: &str, cards: &BTreeMap<String, String>) -> Result<WcsCache, String> {
    let epoch = parse_f64(cards, "EPOCH").unwrap_or(2000.0);
    let crval = [
        parse_f64(cards, "CRVAL1")?,
        parse_f64(cards, "CRVAL2")?,
    ];
    let crpix = [parse_f64(cards, "CRPIX1")?, parse_f64(cards, "CRPIX2")?];
    let cd = [
        [parse_f64(cards, "CD1_1")?, parse_f64(cards, "CD1_2")?],
        [parse_f64(cards, "CD2_1")?, parse_f64(cards, "CD2_2")?],
    ];
    let prev = std::fs::read_to_string(format!("/app/state/wcs-cache/{}.json", run_id))
        .ok()
        .and_then(|raw| serde_json::from_str::<WcsCache>(&raw).ok())
        .map(|w| w.wcs_revision)
        .unwrap_or(0);
    Ok(WcsCache {
        run_id: run_id.to_string(),
        header_epoch: epoch,
        ctype: [
            cards.get("CTYPE1").cloned().unwrap_or_else(|| "RA---TAN".into()),
            cards.get("CTYPE2").cloned().unwrap_or_else(|| "DEC--TAN".into()),
        ],
        crval,
        crpix,
        cd,
        wcs_revision: prev + 1,
    })
}
