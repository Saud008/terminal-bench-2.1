use clap::Parser;
use std::fs;
use std::path::PathBuf;
use vradar_stitch::models::ScanBundle;
use vradar_stitch::ndjson_writer;
use vradar_stitch::scan_manifest;
use vradar_stitch::site_manifest;
use vradar_stitch::stitched_report;
use vradar_stitch::tilt_rank;

#[derive(Parser)]
#[command(name = "vrstctl", about = "Weather radar PPI tilt volume stitch reporter")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(clap::Subcommand)]
enum Command {
    Stitch {
        #[arg(long)]
        bundle: String,
        #[arg(long)]
        token: String,
        #[arg(long)]
        dest: PathBuf,
    },
}

fn fixture_root() -> PathBuf {
    std::env::var("VRST_FIXTURE_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(vradar_stitch::DEFAULT_FIXTURE_ROOT))
}

fn load_bundle(name: &str) -> ScanBundle {
    let path = fixture_root().join(name).join("bundle.json");
    scan_manifest::read_scan_bundle(&path).expect("read scan bundle")
}

fn main() {
    let cli = Cli::parse();
    match cli.command {
        Command::Stitch { bundle, token, dest } => {
            let mut pack = load_bundle(&bundle);
            fs::create_dir_all(vradar_stitch::VAR_ROOT).unwrap();
            site_manifest::write_site_bind(&token, &pack).expect("site bind");
            tilt_rank::sort_tilts_by_elevation(&mut pack.tilt_scans);
            let rows = ndjson_writer::materialize_gates(&pack);
            ndjson_writer::write_gate_buffer(&token, &pack, &rows).expect("write gate buffer");
            let report = stitched_report::build_stitched_report(&token, &pack, &rows);
            fs::write(dest, serde_json::to_string_pretty(&report).unwrap()).unwrap();
        }
    }
}
