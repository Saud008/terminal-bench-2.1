use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "avsccompat")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Ingest {
        #[arg(long)]
        schema_dir: PathBuf,
        #[arg(long)]
        pairs: PathBuf,
        #[arg(long)]
        staging: PathBuf,
    },
    Export {
        #[arg(long)]
        staging: PathBuf,
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.cmd {
        Cmd::Ingest {
            schema_dir,
            pairs,
            staging,
        } => match crate::registry_store::ingest_pairs(&schema_dir, &pairs, &staging) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("ingest error: {e}");
                1
            }
        },
        Cmd::Export { staging, out } => match crate::risk_report::export_report(&staging, &out) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("export error: {e}");
                1
            }
        },
    };
    std::process::exit(code);
}
