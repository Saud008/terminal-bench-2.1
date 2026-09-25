use clap::Parser;
use framecore::{publish_export, run_ingest, run_replay};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(name = "udpctl")]
struct Cli {
    #[command(subcommand)]
    cmd: Command,
}

#[derive(clap::Subcommand, Debug)]
enum Command {
    Ingest {
        #[arg(long)]
        bundle: PathBuf,
        #[arg(long)]
        seed: u64,
    },
    Export {
        #[arg(long)]
        export: PathBuf,
    },
    Replay {
        #[arg(long)]
        bundle: PathBuf,
        #[arg(long)]
        seed: u64,
        #[arg(long)]
        export: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.cmd {
        Command::Ingest { bundle, seed } => run_ingest(&bundle, seed).map(|_| ()),
        Command::Export { export } => publish_export(&export).map(|_| ()),
        Command::Replay {
            bundle,
            seed,
            export,
        } => run_replay(&bundle, seed, &export).map(|_| ()),
    };
    match result {
        Ok(()) => {}
        Err(err) => {
            eprintln!("udpctl failed: {err}");
            std::process::exit(1);
        }
    }
}
