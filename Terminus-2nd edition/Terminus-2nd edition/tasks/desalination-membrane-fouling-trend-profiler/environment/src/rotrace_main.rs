use rotrace_profiler::d9_c5anchor;
use rotrace_profiler::d9_f1bind;
use rotrace_profiler::d9_g4bridge;
use rotrace_profiler::d9_l7emit;
use rotrace_profiler::d9_m2lineage;
use rotrace_profiler::d9_p3norm;
use rotrace_profiler::d9_r8load;
use rotrace_profiler::d9_s6trend;
use rotrace_profiler::types::{
    CleaningBuffer, Config, MembraneBatch, NdpGridRow, ReadingRow, StagedReading, TrendScratch,
};
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
        "load-readings" => load_readings(&cfg, &args),
        "bind-cleaning" => bind_cleaning(&cfg, &args),
        "normalize-ndp" => normalize_ndp(&cfg, &args),
        "score-trends" => score_trends(&cfg, &args),
        "publish-chronicle" => publish_chronicle(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/rotrace.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: rotrace load-readings|bind-cleaning|normalize-ndp|score-trends|publish-chronicle ...");
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

fn load_readings(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut stream = String::new();
    let mut cal_table = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--stream" if i + 1 < args.len() => {
                stream = args[i + 1].clone();
                i += 2;
            }
            "--cal-table" if i + 1 < args.len() => {
                cal_table = args[i + 1].clone();
                i += 2;
            }
            _ => i += 1,
        }
    }
    if stream.is_empty() {
        eprintln!("--stream required");
        return Err(2);
    }
    let overrides = load_cal_overrides(&cal_table);
    d9_r8load::load_readings(cfg, &run_id, &PathBuf::from(stream), &overrides).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn load_cal_overrides(path: &str) -> HashMap<u32, f64> {
    let chosen = if path.is_empty() {
        rotrace_profiler::cal_table_path()
    } else {
        Some(path.to_string())
    };
    let Some(p) = chosen else {
        return HashMap::new();
    };
    let raw = fs::read_to_string(p).unwrap_or_default();
    let mut out = HashMap::new();
    for line in raw.lines().skip(1) {
        let cols: Vec<&str> = line.split(',').collect();
        if cols.len() >= 2 {
            if let (Ok(h), Ok(v)) = (cols[0].parse::<u32>(), cols[1].parse::<f64>()) {
                out.insert(h, v);
            }
        }
    }
    out
}

fn bind_cleaning(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut events = String::new();
    let mut membrane = String::new();
    let mut train_id = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--events" if i + 1 < args.len() => {
                events = args[i + 1].clone();
                i += 2;
            }
            "--membrane" if i + 1 < args.len() => {
                membrane = args[i + 1].clone();
                i += 2;
            }
            "--train-id" if i + 1 < args.len() => {
                train_id = args[i + 1].clone();
                i += 2;
            }
            _ => i += 1,
        }
    }
    if events.is_empty() || membrane.is_empty() || train_id.is_empty() {
        eprintln!("--events, --membrane, and --train-id required");
        return Err(2);
    }
    d9_f1bind::bind_cleaning(
        cfg,
        &run_id,
        &PathBuf::from(events),
        &PathBuf::from(membrane),
        &train_id,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn read_pressure_rows(cfg: &Config, run_id: &str) -> Result<Vec<StagedReading>, i32> {
    let path = format!("{}/{}.jsonl", cfg.pressure_buffer_dir, run_id);
    let raw = fs::read_to_string(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let mut out = Vec::new();
    for line in raw.lines().skip(1) {
        out.push(serde_json::from_str(line).map_err(|e| {
            eprintln!("{e}");
            1
        })?);
    }
    Ok(out)
}

fn read_cleaning_buffer(cfg: &Config, run_id: &str) -> Result<CleaningBuffer, i32> {
    let path = format!("{}/{}.json", cfg.cleaning_buffer_dir, run_id);
    let raw = fs::read_to_string(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn normalize_ndp(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let staged = read_pressure_rows(cfg, &run_id)?;
    let cleaning = read_cleaning_buffer(cfg, &run_id)?;
    let raw_rows: Vec<ReadingRow> = staged
        .into_iter()
        .map(|r| ReadingRow {
            hour_index: r.hour_index,
            batch_id: r.batch_id,
            pressure_bar: r.pressure_bar,
            salinity_ppt: r.salinity_ppt,
            flow_m3h: r.flow_m3h,
            temperature_c: r.temperature_c,
            sensor_flags: r.sensor_flags,
            cal_offset_ppt: r.cal_offset_ppt,
        })
        .collect();
    let bridged = d9_g4bridge::bridge_readings(&raw_rows);
    let mut p_base_map = d9_m2lineage::initial_bases(&cleaning.batches);
    let mut grid = Vec::new();
    for row in &bridged {
        let batch_id = d9_m2lineage::batch_for_hour(row.hour_index, &cleaning.batches)
            .unwrap_or_else(|| row.batch_id.clone());
        let norm = d9_m2lineage::resolve_norm(&batch_id, &cleaning.batches).map_err(|e| {
            eprintln!("{e}");
            1
        })?;
        if d9_c5anchor::is_reset_hour(row.hour_index, &cleaning.cleaning_events) {
            p_base_map.insert(batch_id.clone(), row.pressure_bar);
        }
        let p_base = *p_base_map.get(&batch_id).unwrap_or(&norm.p_base);
        let sal = d9_c5anchor::apply_cal_offset(row.salinity_ppt, row.cal_offset_ppt);
        let ndp_raw = d9_p3norm::compute_ndp(
            row.pressure_bar,
            p_base,
            row.temperature_c,
            norm.t_ref,
            row.flow_m3h,
            norm.q_ref,
            norm.alpha,
            norm.beta,
            sal,
        );
        let ndp = (ndp_raw * 10000.0).round() / 10000.0;
        grid.push(NdpGridRow {
            hour_index: row.hour_index,
            batch_id,
            ndp,
            salinity_ppt: sal,
            pressure_bar: row.pressure_bar,
        });
    }
    let out = format!("{}/{}.json", cfg.ndp_grid_dir, run_id);
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

fn score_trends(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut window = cfg.default_slope_window_hours;
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--slope-window" && i + 1 < args.len() {
            window = args[i + 1].parse().unwrap_or(window);
            i += 2;
        } else {
            i += 1;
        }
    }
    let grid_path = format!("{}/{}.json", cfg.ndp_grid_dir, run_id);
    let grid: Vec<NdpGridRow> = serde_json::from_str(
        &fs::read_to_string(&grid_path).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let scratch = d9_s6trend::score_trends(&run_id, window, &grid);
    let out = format!("{}/{}.json", cfg.trend_scratch_dir, run_id);
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

fn publish_chronicle(cfg: &Config, args: &[String]) -> Result<(), i32> {
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
    let scratch_path = format!("{}/{}.json", cfg.trend_scratch_dir, run_id);
    let scratch: TrendScratch = serde_json::from_str(
        &fs::read_to_string(&scratch_path).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let cleaning = read_cleaning_buffer(cfg, &run_id)?;
    let grid_path = format!("{}/{}.json", cfg.ndp_grid_dir, run_id);
    let grid: Vec<NdpGridRow> = serde_json::from_str(
        &fs::read_to_string(&grid_path).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let chronicle = d9_l7emit::build_chronicle(&run_id, &cleaning.train_id, &scratch, &grid, &cleaning.batches);
    fs::write(
        &output,
        serde_json::to_string_pretty(&chronicle).map_err(|e| {
            eprintln!("{e}");
            1
        })?,
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
