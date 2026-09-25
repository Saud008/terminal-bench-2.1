use water_dose_audit::wv_qb;
use water_dose_audit::wv_qd;
use water_dose_audit::wv_qc;
use water_dose_audit::wv_qg;
use water_dose_audit::wv_qi;
use water_dose_audit::wv_qa;
use water_dose_audit::wv_qe;
use water_dose_audit::plant_schema::{ChemicalDoseRow, Config, ShiftBundle};
use water_dose_audit::wv_qh;
use water_dose_audit::wv_qj;
use water_dose_audit::wv_qf;
use water_dose_audit::shift_io;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

fn main() {
    if let Err(code) = run() {
        std::process::exit(code);
    }
}

fn run() -> Result<(), i32> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        usage();
        return Err(2);
    }
    let cfg = load_config()?;
    match args[1].as_str() {
        "load-shift-dose" => run_ingest(&cfg, &args),
        "export-breach-atlas" => run_publish_safety(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/wtcdctl.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: wtcdctl load-shift-dose|export-breach-atlas ...");
}

fn ledger_path(cfg: &Config, plant_id: &str) -> PathBuf {
    PathBuf::from(&cfg.ledger_dir).join(format!("{plant_id}.json"))
}

fn run_ingest(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (plant_id, shift) = parse_plant_shift(args, 2)?;
    let path = shift_io::bundle_path(&shift);
    let bundle = shift_io::load_bundle(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    if bundle.plant_id != plant_id {
        eprintln!("plant mismatch");
        return Err(1);
    }
    let ledger = ledger_path(cfg, &plant_id);
    let prev = wv_qi::read_revision_token(ledger.to_str().unwrap());
    let rows = compute_doses(&bundle, cfg).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    wv_qi::write_ledger(
        ledger.to_str().unwrap(),
        &plant_id,
        &shift,
        &bundle.as_of,
        prev.as_str(),
        rows,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn compute_doses(bundle: &ShiftBundle, cfg: &Config) -> Result<Vec<ChemicalDoseRow>, String> {
    let flow_by_min = build_flow_series(bundle);
    let turb_by_min = build_turbidity_series(bundle);
    let mut out = Vec::new();
                let max_min = bundle
                    .flow_readings
                    .iter()
                    .map(|r| r.minute)
                    .chain(bundle.turbidity_readings.iter().map(|r| r.minute))
                    .max()
                    .unwrap_or(0);
                for chem in &bundle.chemicals {
                    let mut concs = Vec::new();
                    let mut flows = Vec::new();
                    let mut total = 0.0_f64;
                    let mut override_applied = false;
                    let mut contact_excluded = 0u32;
                    for minute in 0..=max_min {
                        let flow = flow_by_min.get(&minute).copied().unwrap_or(0.0);
                        if !wv_qg::minute_eligible(flow, bundle.min_flow_lpm) {
                            contact_excluded += 1;
                            continue;
                        }
                        let turb = turb_by_min.get(&minute).copied().unwrap_or(bundle.target_turbidity_ntu);
            let mut conc = wv_qb::normalize_mg_per_l(chem.concentration, &chem.unit);
                        for ov in &bundle.overrides {
                            if ov.chem_id == chem.chem_id
                                && wv_qe::override_allowed(
                                    &ov.user,
                                    &ov.role,
                                    &cfg.authorized_roles,
                                    &cfg.denylist,
                                )
                            {
                                conc *= ov.factor;
                                override_applied = true;
                            }
                        }
                        let uplift = wv_qd::turbidity_uplift(turb, bundle.target_turbidity_ntu);
                        let raw = wv_qd::minute_dose_mg(flow, conc, uplift);
                        total += wv_qh::apply_minute_cap(raw, bundle.minute_dose_cap_mg);
                        concs.push(conc);
                        flows.push(flow);
                    }
                    let weighted = wv_qd::flow_weighted_mg_per_l(&concs, &flows);
                    let fp = wv_qa::arc_ppm_fingerprint(
                        &chem.chem_id,
                        &chem.lot_code,
                        &bundle.as_of,
                    );
                    out.push(ChemicalDoseRow {
                        chem_id: chem.chem_id.clone(),
                        arc_tok: fp,
                        weighted_conc_mg_l: weighted,
                        total_dose_mg: total,
                        max_dose_mg: chem.max_dose_mg,
                        contact_excluded_minutes: contact_excluded,
                        override_applied,
                    });
                }
                Ok(out)
            }

fn build_flow_series(bundle: &ShiftBundle) -> HashMap<u32, f64> {
    let mut by_sensor: HashMap<String, Vec<(u32, Option<f64>)>> = HashMap::new();
    for r in &bundle.flow_readings {
        let val = if r.status == "ok" {
            Some(wv_qc::m3h_to_lpm(r.m3_h))
        } else {
            None
        };
        by_sensor.entry(r.sensor_id.clone()).or_default().push((r.minute, val));
    }
    let mut out = HashMap::new();
    for (_sid, mut rows) in by_sensor {
        rows.sort_by_key(|r| r.0);
        let filled = wv_qf::forward_fill(&rows.iter().map(|(_, v)| *v).collect::<Vec<_>>());
        for (i, (minute, _)) in rows.iter().enumerate() {
            out.insert(*minute, filled[i]);
        }
    }
    out
}

fn build_turbidity_series(bundle: &ShiftBundle) -> HashMap<u32, f64> {
    let mut by_sensor: HashMap<String, Vec<(u32, Option<f64>)>> = HashMap::new();
    for r in &bundle.turbidity_readings {
        let val = if r.status == "ok" {
            Some(r.ntu)
        } else {
            None
        };
        by_sensor.entry(r.sensor_id.clone()).or_default().push((r.minute, val));
    }
    let mut out = HashMap::new();
    for (_sid, mut rows) in by_sensor {
        rows.sort_by_key(|r| r.0);
        let filled = wv_qf::forward_fill(&rows.iter().map(|(_, v)| *v).collect::<Vec<_>>());
        for (i, (minute, _)) in rows.iter().enumerate() {
            out.insert(*minute, filled[i]);
        }
    }
    out
}

fn run_publish_safety(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let (plant_id, output) = parse_plant_output(args, 2)?;
    let ledger = ledger_path(cfg, &plant_id);
    let report = wv_qj::build_safety(ledger.to_str().unwrap(), &plant_id).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    wv_qj::write_safety(&PathBuf::from(output), &report).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_plant_shift(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut plant_id = String::new();
    let mut shift = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--plant" if i + 1 < args.len() => {
                plant_id = args[i + 1].clone();
                i += 2;
            }
            "--shift" if i + 1 < args.len() => {
                shift = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if plant_id.is_empty() || shift.is_empty() {
        eprintln!("--plant and --shift required");
        return Err(2);
    }
    Ok((plant_id, shift))
}

fn parse_plant_output(args: &[String], start: usize) -> Result<(String, String), i32> {
    let mut plant_id = String::new();
    let mut output = String::new();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--plant" if i + 1 < args.len() => {
                plant_id = args[i + 1].clone();
                i += 2;
            }
            "--output" if i + 1 < args.len() => {
                output = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if plant_id.is_empty() || output.is_empty() {
        eprintln!("--plant and --output required");
        return Err(2);
    }
    Ok((plant_id, output))
}
