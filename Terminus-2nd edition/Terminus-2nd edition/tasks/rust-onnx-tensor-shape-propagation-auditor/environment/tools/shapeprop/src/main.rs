use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "shapeprop")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    BatchPropagate {
        #[arg(long = "graph-batch")]
        graph_dir: PathBuf,
        #[arg(long)]
        ledger: PathBuf,
    },
    EmitViolations {
        #[arg(long)]
        ledger: PathBuf,
        #[arg(long = "graph-batch")]
        graph_dir: PathBuf,
        #[arg(long)]
        report: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.cmd {
        Cmd::BatchPropagate { graph_dir, ledger } => match staging_store::dir_load_rows(&graph_dir, &ledger) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("batch-propagate error: {e}");
                1
            }
        },
        Cmd::EmitViolations {
            ledger,
            graph_dir,
            report,
        } => match audit_export::stage_audit_out(&ledger, &graph_dir, &report) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("emit-violations error: {e}");
                1
            }
        },
    };
    std::process::exit(code);
}
