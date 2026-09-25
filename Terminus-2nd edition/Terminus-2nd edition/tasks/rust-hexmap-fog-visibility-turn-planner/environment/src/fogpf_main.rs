use hex_fog_planner::tb3_rout;
use hex_fog_planner::tb3_mdist;
use hex_fog_planner::tb3_vlay;
use hex_fog_planner::tb3_sray;
use hex_fog_planner::hx_place;
use hex_fog_planner::tb3_pclk;
use hex_fog_planner::tb3_scope;
use hex_fog_planner::types::{BoardDoc, BoardRoster, Config, FogMask, RayRow};
use std::fs;
use std::io::Write;
use std::path::Path;

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
        "load-board" => load_board(&cfg, &args),
        "place-units" => place_units(&cfg, &args),
        "resolve-los" => resolve_los(&cfg, &args),
        "reveal-fog" => reveal_fog(&cfg, &args),
        "seal-atlas" => seal_atlas(&cfg, &args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn usage() {
    eprintln!("usage: fogpf load-board|place-units|resolve-los|reveal-fog|seal-atlas ...");
}

fn load_config() -> Result<Config, i32> {
    let raw = fs::read_to_string("/app/config/tb3-cli.json").map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
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

fn board_arg(args: &[String]) -> Result<String, i32> {
    let mut board = String::new();
    let mut i = 2;
    while i < args.len() {
        if args[i] == "--board" && i + 1 < args.len() {
            board = args[i + 1].clone();
            i += 2;
        } else {
            i += 1;
        }
    }
    if board.is_empty() {
        eprintln!("--board required");
        return Err(2);
    }
    Ok(board)
}

fn roster_path(cfg: &Config, run_id: &str) -> String {
    format!("{}/{}.json", cfg.board_roster_dir, run_id)
}

fn load_roster(cfg: &Config, run_id: &str) -> Result<BoardRoster, i32> {
    let raw = fs::read_to_string(roster_path(cfg, run_id)).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn save_roster(cfg: &Config, roster: &BoardRoster) -> Result<(), i32> {
    let out = roster_path(cfg, &roster.run_id);
    fs::create_dir_all(Path::new(&cfg.board_roster_dir)).ok();
    fs::write(&out, serde_json::to_string_pretty(roster).unwrap()).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}

fn load_board(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let board_path = board_arg(args)?;
    let text = fs::read_to_string(&board_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let doc: BoardDoc = serde_json::from_str(&text).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let mut roster = hx_place::roster_from_board(&run_id, doc);
    tb3_pclk::on_load_board(&mut roster);
    save_roster(cfg, &roster)
}

fn place_units(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut roster = load_roster(cfg, &run_id)?;
    hx_place::refresh_units(&mut roster);
    save_roster(cfg, &roster)
}

fn resolve_los(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let roster = load_roster(cfg, &run_id)?;
    let elev = tb3_sray::elev_map(&roster.cells);
    fs::create_dir_all(Path::new(&cfg.los_ray_dir)).ok();
    let out = format!("{}/{}.jsonl", cfg.los_ray_dir, run_id);
    let mut f = fs::File::create(&out).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    for unit in &roster.units {
        let radius = tb3_scope::vision_radius(&unit.class);
        for cell in &roster.cells {
            let dist = tb3_mdist::cube_distance(unit.q, unit.r, cell.q, cell.r);
            let in_radius = dist <= radius;
            let clear = tb3_sray::clear_los(unit.q, unit.r, cell.q, cell.r, &elev);
            let row = RayRow {
                run_id: run_id.clone(),
                unit_id: unit.unit_id.clone(),
                q: cell.q,
                r: cell.r,
                in_radius,
                clear_los: clear,
            };
            writeln!(f, "{}", serde_json::to_string(&row).unwrap()).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
    }
    Ok(())
}

fn reveal_fog(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let mut roster = load_roster(cfg, &run_id)?;
    tb3_pclk::on_reveal_fog(&mut roster);
    let mask_path = format!("{}/{}.json", cfg.fog_mask_dir, run_id);
    let prior = fs::read_to_string(&mask_path)
        .ok()
        .and_then(|raw| serde_json::from_str::<FogMask>(&raw).ok());
    let mut mask = tb3_vlay::reveal(&roster, prior.as_ref());
    mask.fog_generation = roster.fog_generation;
    fs::create_dir_all(Path::new(&cfg.fog_mask_dir)).ok();
    fs::write(&mask_path, serde_json::to_string_pretty(&mask).unwrap()).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    save_roster(cfg, &roster)?;
    Ok(())
}

fn seal_atlas(cfg: &Config, args: &[String]) -> Result<(), i32> {
    let run_id = run_id_arg(args)?;
    let roster = load_roster(cfg, &run_id)?;
    let mask_path = format!("{}/{}.json", cfg.fog_mask_dir, run_id);
    let raw = fs::read_to_string(&mask_path).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let mask: FogMask = serde_json::from_str(&raw).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    let atlas = tb3_rout::seal_atlas(&roster, &mask);
    fs::create_dir_all(Path::new(&cfg.output_dir)).ok();
    let out = format!("{}/{}-fog-atlas.json", cfg.output_dir, run_id);
    fs::write(&out, serde_json::to_string_pretty(&atlas).unwrap()).map_err(|e| {
        eprintln!("{e}");
        1
    })?;
    Ok(())
}
