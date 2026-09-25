use clap::{Parser, Subcommand};
use std::path::PathBuf;
use xanes_core::mu_window_seal::run_close;

#[derive(Parser)]
#[command(name = "xanesctl")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Close {
        #[arg(long)]
        trace: PathBuf,
        #[arg(long)]
        windows: PathBuf,
        #[arg(long)]
        export: PathBuf,
        #[arg(long)]
        seed: Option<String>,
    },
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Close {
            trace,
            windows,
            export,
            seed,
        } => {
            let code = run_close(&trace, &windows, &export, seed.as_deref());
            std::process::exit(code);
        }
    }
}
