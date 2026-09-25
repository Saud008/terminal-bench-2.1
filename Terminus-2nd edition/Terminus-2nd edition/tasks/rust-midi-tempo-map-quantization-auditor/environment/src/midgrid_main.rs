use midi_tempo_auditor::bline_ex;
use midi_tempo_auditor::bline_mf;
use midi_tempo_auditor::bline_tm;
use midi_tempo_auditor::bline_lg;
use midi_tempo_auditor::bline_qn;
use midi_tempo_auditor::bline_pl;
use midi_tempo_auditor::bline_wc;
use midi_tempo_auditor::types::{ChartManifest, Config, GridRow, NoteStageRow};
use std::fs;
use std::io::Write;
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
        "load-chart" => load_chart(&cfg, &args),
        "stage-tempo" => stage_tempo(&cfg, &args),
        "build-grid" => build_grid(&cfg, &args),
        "quantize-notes" => quantize_notes(&cfg, &args),
        "emit-audit" => emit_audit(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/midgrid.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: midgrid load-chart|stage-tempo|build-grid|quantize-notes|emit-audit ...");
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

fn load_chart(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut chart = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--chart" && i + 1 < args.len() {
            chart = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if chart.is_empty() {
        eprintln!("--chart required");
        return Err(2);
    }
    let text = fs::read_to_string(&chart).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let doc = bline_mf::parse_chart(&text).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let prev = fs::read_to_string(format!("{}/{}.json", cfg.chart_manifest_dir, run_id))
        .ok()
        .and_then(|raw| serde_json::from_str::<ChartManifest>(&raw).ok())
        .map(|s| s.manifest_revision)
        .unwrap_or(0);
    let ledger = ChartManifest {
        run_id: run_id.clone(),
        chart_id: bline_mf::normalize_id(&doc.chart_id),
        ppq: doc.ppq,
        quant_divisor: doc.quant_divisor,
        tempo_events: doc.tempo_events,
        time_sigs: doc.time_sigs,
        notes: doc.notes,
        manifest_revision: prev + 1,
    };
    let out = format!("{}/{}.json", cfg.chart_manifest_dir, run_id);
    fs::write(&out, serde_json::to_string_pretty(&ledger).unwrap()).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn load_manifest(cfg: &Config, run_id: &str) -> Result<ChartManifest, i32> {
    let path = format!("{}/{}.json", cfg.chart_manifest_dir, run_id);
    let raw = fs::read_to_string(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn stage_tempo(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let ledger = load_manifest(cfg, &run_id)?;
    bline_pl::stage_tempo(cfg, &run_id, &ledger.tempo_events).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn build_grid(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let ledger = load_manifest(cfg, &run_id)?;
    let mut divisor = ledger.quant_divisor;
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--quant" && i + 1 < args.len() {
            divisor = args[i + 1].parse().unwrap_or(divisor);
            i += 2;
        } else {
            i += 1;
        }
    }
    if let Some(o) = midi_tempo_auditor::quant_divisor_override() {
        divisor = o;
    }
    let tempo_raw = fs::read_to_string(format!("{}/{}.jsonl", cfg.tempo_stage_dir, run_id)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let mut tempo_lines = tempo_raw.lines();
    let _hdr = tempo_lines.next();
    let mut tempos = Vec::new();
    for line in tempo_lines {
        tempos.push(serde_json::from_str(line).map_err(|e| {
            eprintln!("{e}");
            1
        })?);
    }
    let out_path = format!("{}/{}.jsonl", cfg.grid_stage_dir, run_id);
    let mut f = fs::File::create(&out_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    writeln!(f, "{{\"run_id\":\"{run_id}\",\"quant_divisor\":{divisor}}}").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let mut markers: Vec<u64> = tempos.iter().map(|t: &midi_tempo_auditor::types::TempoEvent| t.tick).collect();
    for ts in &ledger.time_sigs {
        markers.push(ts.tick);
    }
    for n in &ledger.notes {
        markers.push(n.tick);
    }
    markers.sort_unstable();
    markers.dedup();
    for tick in markers {
        let meter = bline_tm::active_meter(tick, &ledger.time_sigs);
        let tpb = bline_tm::ticks_per_beat(ledger.ppq, &meter);
        let seconds = bline_wc::tick_to_seconds(tick, ledger.ppq, &tempos);
        let beat = tick as f64 / tpb as f64;
        let row = GridRow {
            tick,
            seconds,
            beat_index: beat,
            ticks_per_beat: tpb,
        };
        let js = serde_json::to_string(&row).map_err(|e| {
            eprintln!("{e}");
            1
        })?;
        writeln!(f, "{js}").map_err(|e| {
            eprintln!("{e}");
            1
        })?;
    }
    Ok(())
}

fn quantize_notes(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let ledger = load_manifest(cfg, &run_id)?;
    let rejected = bline_lg::rejected_ids(&ledger.notes);
    let mut rows: Vec<NoteStageRow> = ledger
        .notes
        .iter()
        .map(|n| {
            let q = bline_qn::quantize_tick(n.tick, ledger.ppq, &ledger.time_sigs, ledger.quant_divisor);
            NoteStageRow {
                id: n.id.clone(),
                lane: n.lane,
                raw_tick: n.tick,
                quantized_tick: q,
                rejected_overlap: rejected.contains(&n.id),
            }
        })
        .collect();
    rows.sort_by(|a, b| a.id.cmp(&b.id));
    let out_path = format!("{}/{}.jsonl", cfg.note_stage_dir, run_id);
    let mut f = fs::File::create(&out_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    writeln!(
        f,
        "{{\"run_id\":\"{run_id}\",\"chart_id\":\"{}\"}}",
        ledger.chart_id
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    for row in rows {
        let js = serde_json::to_string(&row).map_err(|e| {
            eprintln!("{e}");
            1
        })?;
        writeln!(f, "{js}").map_err(|e| {
            eprintln!("{e}");
            1
        })?;
    }
    Ok(())
}

fn emit_audit(cfg: &Config, args: &[String]) -> Result<(), i32> {
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
    let ledger = load_manifest(cfg, &run_id)?;
    bline_ex::write_audit(cfg, &run_id, &ledger, &PathBuf::from(output)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
