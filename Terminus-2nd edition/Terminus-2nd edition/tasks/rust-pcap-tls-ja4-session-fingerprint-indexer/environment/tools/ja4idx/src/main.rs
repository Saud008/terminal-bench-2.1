use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "ja4idx")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    #[command(name = "intake")]
    Intake {
        #[arg(long)]
        capsules_dir: PathBuf,
        #[arg(long = "ledger")]
        ledger: PathBuf,
    },
    #[command(name = "emit")]
    Emit {
        #[arg(long = "ledger")]
        ledger: PathBuf,
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.cmd {
        Cmd::Intake {
            capsules_dir,
            ledger,
        } => match ledger_store::persist_capsule_ledger(&capsules_dir, &ledger) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("intake error: {e}");
                1
            }
        },
        Cmd::Emit { ledger, out } => match index_emit::publish_ledger_report(&ledger, &out) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("emit error: {e}");
                1
            }
        },
    };
    std::process::exit(code);
}
