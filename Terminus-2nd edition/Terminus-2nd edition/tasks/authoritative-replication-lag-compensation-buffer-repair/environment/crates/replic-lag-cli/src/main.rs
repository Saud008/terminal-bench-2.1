mod util;

use clap::{Parser, Subcommand};
use replic_lag_core::{export_snapshot_bundle, ingest_trace, run_simulation};
use std::path::PathBuf;

#[allow(dead_code)]
fn _keep_util_linked() {
    let _ = util::ignore_tick_hint(0);
}

#[derive(Parser)]
#[command(name = "replag-sim", about = "Authoritative replication lag compensation simulator")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Ingest a JSONL packet trace into the ledger database.
    Ingest {
        #[arg(long)]
        trace: PathBuf,
        #[arg(long, default_value = "/app/data/replic.db")]
        db: PathBuf,
        #[arg(long, default_value = "/app/state/ingest-manifest.json")]
        manifest: PathBuf,
    },
    /// Simulate lag compensation and input buffering from a trace.
    Simulate {
        #[arg(long)]
        trace: PathBuf,
        #[arg(long, default_value = "/app/data/replic.db")]
        db: PathBuf,
        #[arg(long, default_value = "/app/state/sim-report.json")]
        report: PathBuf,
        #[arg(long, default_value_t = 0)]
        tick_rate: u64,
    },
    /// Export merged snapshot bundle with integrity chain.
    ExportSnapshot {
        #[arg(long, default_value = "/app/data/replic.db")]
        db: PathBuf,
        #[arg(long, default_value = "/app/output/snapshot-bundle.json")]
        bundle: PathBuf,
        #[arg(long, default_value = "/app/state/export-audit.json")]
        audit: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Ingest {
            trace,
            db,
            manifest,
        } => match ingest_trace(&trace, &db, &manifest) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("ingest failed: {err}");
                1
            }
        },
        Commands::Simulate {
            trace,
            db,
            report,
            tick_rate,
        } => match run_simulation(&trace, &db, &report, tick_rate) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("simulate failed: {err}");
                1
            }
        },
        Commands::ExportSnapshot { db, bundle, audit } => {
            match export_snapshot_bundle(&db, &bundle, &audit) {
                Ok(_) => 0,
                Err(err) => {
                    eprintln!("export failed: {err}");
                    1
                }
            }
        }
    };
    std::process::exit(code);
}
