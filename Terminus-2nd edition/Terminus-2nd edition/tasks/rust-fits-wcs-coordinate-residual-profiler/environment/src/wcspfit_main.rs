use fits_wcs_profiler::fcard_lex;
use fits_wcs_profiler::det_rows;
use fits_wcs_profiler::rms_atlas;
use fits_wcs_profiler::gc_match;
use fits_wcs_profiler::types::Config;
use fits_wcs_profiler::wmeter_hdr;
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
        "parse-header" => parse_header(&cfg, &args),
        "buffer-detections" => buffer_detections(&cfg, &args),
        "crossmatch" => crossmatch(&cfg, &args),
        "profile-residuals" => profile_residuals(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/wcspfit.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("usage: wcspfit parse-header|buffer-detections|crossmatch|profile-residuals ...");
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

fn parse_header(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut header = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--header" && i + 1 < args.len() {
            header = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if header.is_empty() {
        eprintln!("--header required");
        return Err(2);
    }
    let text = fs::read_to_string(&header).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let cards = fcard_lex::parse_cards(&text).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let wcs = wmeter_hdr::extract_wcs(&run_id, &cards).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let out = format!("{}/{}.json", cfg.wcs_cache_dir, run_id);
    fs::write(&out, serde_json::to_string_pretty(&wcs).unwrap()).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn load_wcs(cfg: &Config, run_id: &str) -> Result<fits_wcs_profiler::types::WcsCache, i32> {
    let path = format!("{}/{}.json", cfg.wcs_cache_dir, run_id);
    let raw = fs::read_to_string(&path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn buffer_detections(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let wcs = load_wcs(cfg, &run_id)?;
    let mut catalog = String::new();
    let mut detections = String::new();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--catalog" if i + 1 < args.len() => {
                catalog = args[i + 1].clone();
                i += 2;
            }
            "--detections" if i + 1 < args.len() => {
                detections = args[i + 1].clone();
                i += 2;
            }
            _ => i += 1,
        }
    }
    if catalog.is_empty() || detections.is_empty() {
        eprintln!("--catalog and --detections required");
        return Err(2);
    }
    det_rows::buffer_detections(
        cfg,
        &run_id,
        &wcs,
        &PathBuf::from(catalog),
        &PathBuf::from(detections),
    )
    .map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn crossmatch(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let wcs = load_wcs(cfg, &run_id)?;
    gc_match::crossmatch_run(cfg, &run_id, &wcs).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn profile_residuals(cfg: &Config, args: &[String]) -> Result<(), i32> {
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
    rms_atlas::write_atlas(cfg, &run_id, &PathBuf::from(output)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
