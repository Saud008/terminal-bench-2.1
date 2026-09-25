use kiln_energy_profiler::c7_h3score;
use kiln_energy_profiler::c7_f2bind;
use kiln_energy_profiler::c7_f6rows;
use kiln_energy_profiler::c7_g5span;
use kiln_energy_profiler::c7_l8emit;
use kiln_energy_profiler::c7_p4bias;
use kiln_energy_profiler::c7_t6rows;
use kiln_energy_profiler::types::{Config, FuelBatch, ProbeWindow, StagedTelemetry};
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
        "load-probes" => load_probes(&cfg, &args),
        "bind-fuel" => bind_fuel(&cfg, &args),
        "interpolate-probes" => interpolate_probes(&cfg, &args),
        "score-balance" => score_balance_cmd(&cfg, &args),
        "publish-ledger" => publish_ledger(&cfg, &args), // publish final heat balance ledger
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/kilnbal.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: kilnbal load-probes|bind-fuel|interpolate-probes|score-balance|publish-ledger ...");
}

fn run_id_arg(args: &[String]) -> Result<String, i32> {
    let mut run_id = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--run-id" && i + 1 < args.len() {
            run_id = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if run_id.is_empty() {
        eprintln!("--run-id required");
        return Err(2);
    }
    Ok(run_id)
}

fn load_probes(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut telemetry = String::new();
    let mut cal_table = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--telemetry" if i + 1 < args.len() => {
                telemetry = args[i + 1].clone();
                i += 2;
            }
            "--cal-table" if i + 1 < args.len() => {
                cal_table = args[i + 1].clone();
                i += 2;
            }
            _ => i += 1,
        }
    }
    if telemetry.is_empty() {
        eprintln!("--telemetry required");
        return Err(2);
    }
    let overrides = load_cal_overrides(&cal_table);
    c7_t6rows::load_probes(cfg, &run_id, &PathBuf::from(telemetry), &overrides).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn load_cal_overrides(path: &str) -> Vec<(String, f64)> {
    if path.is_empty() {
        if let Some(p) = kiln_energy_profiler::cal_table_path() {
            return parse_cal_table(&p);
        }
        return Vec::new();
    }
    parse_cal_table(path)
}

fn parse_cal_table(path: &str) -> Vec<(String, f64)> {
    let raw = fs::read_to_string(path).unwrap_or_default();
    let mut out = Vec::new();
    for line in raw.lines().skip(1) {
        let p: Vec<&str> = line.split(',').collect();
        if p.len() >= 2 {
            if let Ok(v) = p[1].parse() {
                out.push((p[0].to_string(), v));
            }
        }
    }
    out
}

fn bind_fuel(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut fuel = String::new();
    let mut clinker = String::new();
    let mut kiln_id = "KILN-01".to_string();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--fuel" if i + 1 < args.len() => {
                fuel = args[i + 1].clone();
                i += 2;
            }
            "--clinker" if i + 1 < args.len() => {
                clinker = args[i + 1].clone();
                i += 2;
            }
            "--kiln-id" if i + 1 < args.len() => {
                kiln_id = args[i + 1].clone();
                i += 2;
            }
            _ => i += 1,
        }
    }
    if fuel.is_empty() || clinker.is_empty() {
        eprintln!("--fuel and --clinker required");
        return Err(2);
    }
    c7_f6rows::bind_fuel_clinker(
        cfg,
        &run_id,
        &PathBuf::from(fuel),
        &PathBuf::from(clinker),
        &kiln_id,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn interpolate_probes(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let tele_path = format!("{}/{}.jsonl", cfg.tele_buffer_dir, run_id);
    let raw = fs::read_to_string(&tele_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let mut staged = Vec::new();
    for line in raw.lines().skip(1) {
        staged.push(serde_json::from_str::<StagedTelemetry>(line).map_err(|e| {
            eprintln!("{e}");
            1
        })?);
    }
    let fuel_path = format!("{}/{}.json", cfg.fuel_buffer_dir, run_id);
    let fuel_doc: serde_json::Value = serde_json::from_str(
        &fs::read_to_string(&fuel_path).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let fuels: Vec<FuelBatch> =
        serde_json::from_value(fuel_doc["fuel_batches"].clone()).map_err(|e| {
            eprintln!("{e}");
            1
        })?;
    let mut points = Vec::new();
    for row in staged {
        let temp_c = c7_p4bias::apply_calibration(row.temp_norm_c, row.cal_offset_c);
        points.push((row.probe_ts, row.probe_id, temp_c));
    }
    let batches = fuels.clone();
    let lookup = move |ts: u64| c7_f2bind::batch_for_probe_ts(&batches, ts);
    let grid = c7_g5span::fill_gaps(points, cfg.grid_step_sec, &lookup);
    let out = format!("{}/{}.json", cfg.probe_grid_dir, run_id);
    fs::write(&out, serde_json::to_string_pretty(&grid).map_err(|e| {
        eprintln!("{e}");
        1
    })?)
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn score_balance_cmd(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut heat_loss_path = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--heat-loss" && i + 1 < args.len() {
            heat_loss_path = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if heat_loss_path.is_empty() {
        eprintln!("--heat-loss required");
        return Err(2);
    }
    let fuel_doc: serde_json::Value = serde_json::from_str(
        &fs::read_to_string(format!("{}/{}.json", cfg.fuel_buffer_dir, run_id)).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let fuels: Vec<FuelBatch> =
        serde_json::from_value(fuel_doc["fuel_batches"].clone()).map_err(|e| {
            eprintln!("{e}");
            1
        })?;
    let clinker: Vec<kiln_energy_profiler::types::ClinkerWindow> =
        serde_json::from_value(fuel_doc["clinker_windows"].clone()).map_err(|e| {
            eprintln!("{e}");
            1
        })?;
    let heat_doc: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&heat_loss_path).map_err(|e| {
            eprintln!("{e}");
            1
        })?)
        .map_err(|e| {
            eprintln!("{e}");
            1
        })?;
    let heat_loss = heat_doc["heat_loss_mj"].as_f64().unwrap_or(0.0);
    let scratch = c7_h3score::score_balance(cfg, &run_id, &fuels, &clinker, heat_loss);
    let out = format!("{}/{}.json", cfg.balance_scratch_dir, run_id);
    fs::write(&out, serde_json::to_string_pretty(&scratch).map_err(|e| {
        eprintln!("{e}");
        1
    })?)
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn publish_ledger(cfg: &Config, args: &[String]) -> Result<(), i32> {
    // publish final heat balance ledger JSON artifact
    let run_id = run_id_arg(args)?;
    let mut output = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--output" && i + 1 < args.len() {
            output = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if output.is_empty() {
        eprintln!("--output required");
        return Err(2);
    }
    let scratch: kiln_energy_profiler::types::BalanceScratch = serde_json::from_str(
        &fs::read_to_string(format!("{}/{}.json", cfg.balance_scratch_dir, run_id)).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let fuel_doc: serde_json::Value = serde_json::from_str(
        &fs::read_to_string(format!("{}/{}.json", cfg.fuel_buffer_dir, run_id)).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let fuels: Vec<FuelBatch> =
        serde_json::from_value(fuel_doc["fuel_batches"].clone()).map_err(|e| {
            eprintln!("{e}");
            1
        })?;
    let kiln_id = fuel_doc["kiln_id"].as_str().unwrap_or("KILN-01").to_string();
    let probes: Vec<ProbeWindow> = serde_json::from_str(
        &fs::read_to_string(format!("{}/{}.json", cfg.probe_grid_dir, run_id)).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let ledger = c7_l8emit::build_ledger(&run_id, &kiln_id, &scratch, fuels, probes);
    fs::write(&output, serde_json::to_string_pretty(&ledger).map_err(|e| {
        eprintln!("{e}");
        1
    })?)
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
