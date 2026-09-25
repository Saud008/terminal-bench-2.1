use std::env;
use std::path::PathBuf;
use std::process;

use hitbox_core::{run_export, run_replay, run_sample, write_report};

fn main() {
    let mut args = env::args().skip(1);
    let cmd = args.next().unwrap_or_else(|| usage());
    match cmd.as_str() {
        "sample" => run_sample_cmd(&mut args),
        "export" => run_export_cmd(&mut args),
        "replay" => run_replay_cmd(&mut args),
        _ => usage(),
    }
}

fn run_sample_cmd(args: &mut impl Iterator<Item = String>) {
    let opts = parse_common(args);
    run_sample(
        &opts.entities,
        &opts.animation,
        opts.tick_rate,
        opts.fps,
        opts.max_tick,
    )
    .unwrap_or_else(|e| {
        eprintln!("sample failed: {e}");
        process::exit(1);
    });
}

fn run_export_cmd(args: &mut impl Iterator<Item = String>) {
    let opts = parse_common(args);
    let report = run_export(&opts.entities, &opts.animation).unwrap_or_else(|e| {
        eprintln!("export failed: {e}");
        process::exit(1);
    });
    write_report(&opts.export, &report).unwrap_or_else(|e| {
        eprintln!("write failed: {e}");
        process::exit(1);
    });
}

fn run_replay_cmd(args: &mut impl Iterator<Item = String>) {
    let opts = parse_common(args);
    let report = run_replay(
        &opts.entities,
        &opts.animation,
        opts.tick_rate,
        opts.fps,
        opts.max_tick,
    )
    .unwrap_or_else(|e| {
        eprintln!("replay failed: {e}");
        process::exit(1);
    });
    write_report(&opts.export, &report).unwrap_or_else(|e| {
        eprintln!("write failed: {e}");
        process::exit(1);
    });
}

struct CommonOpts {
    entities: PathBuf,
    animation: PathBuf,
    export: PathBuf,
    tick_rate: u32,
    fps: u32,
    max_tick: u32,
}

fn parse_common(args: &mut impl Iterator<Item = String>) -> CommonOpts {
    let mut entities = PathBuf::from("/app/fixtures/entities/alpha_entities.json");
    let mut animation = PathBuf::from("/app/fixtures/animations/alpha.jsonl");
    let mut export = PathBuf::from("/app/output/collision-report.json");
    let mut tick_rate = 60u32;
    let mut fps = 30u32;
    let mut max_tick = 120u32;

    while let Some(flag) = args.next() {
        match flag.as_str() {
            "--entities" => entities = PathBuf::from(args.next().expect("--entities value")),
            "--animation" => animation = PathBuf::from(args.next().expect("--animation value")),
            "--export" => export = PathBuf::from(args.next().expect("--export value")),
            "--tick-rate" => tick_rate = args.next().expect("--tick-rate value").parse().expect("u32"),
            "--fps" => fps = args.next().expect("--fps value").parse().expect("u32"),
            "--max-tick" => max_tick = args.next().expect("--max-tick value").parse().expect("u32"),
            _ => usage(),
        }
    }

    CommonOpts {
        entities,
        animation,
        export,
        tick_rate,
        fps,
        max_tick,
    }
}

fn usage() -> ! {
    eprintln!(
        "usage:\n  hitreplay sample --entities PATH --animation PATH [--tick-rate 60] [--fps 30] [--max-tick N]\n  hitreplay export --entities PATH --animation PATH --export PATH\n  hitreplay replay --entities PATH --animation PATH --export PATH [--tick-rate 60] [--fps 30] [--max-tick N]"
    );
    process::exit(2);
}
