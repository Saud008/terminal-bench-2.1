use std::path::PathBuf;

use clap::{Parser, Subcommand};
use nmeapipeline::pipeline;

#[derive(Parser)]
#[command(name = "nmeapipeline")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Merge {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        state: Option<PathBuf>,
    },
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Merge { input, output, state } => {
            if let Err(e) = pipeline::run_merge(&input, &output, state.as_deref()) {
                eprintln!("{e}");
                std::process::exit(1);
            }
        }
    }
}
