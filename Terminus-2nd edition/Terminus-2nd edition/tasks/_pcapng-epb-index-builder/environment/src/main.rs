use clap::{Parser, Subcommand};

use pcap_index::cli;

#[derive(Parser)]
#[command(name = "pcap-index")]
struct App {
    #[command(subcommand)]
    cmd: Command,
}

#[derive(Subcommand)]
enum Command {
    Ingest {
        #[arg(long)]
        input: String,
        #[arg(long, default_value = "/app/state/index.db")]
        db: String,
    },
    Export {
        #[arg(long, default_value = "/app/state/index.db")]
        db: String,
        #[arg(long, default_value = "/app/output/capture-summary.json")]
        out: String,
    },
}

fn main() {
    let app = App::parse();
    let result = match app.cmd {
        Command::Ingest { input, db } => cli::ingest(&input, &db),
        Command::Export { db, out } => cli::export(&db, &out),
    };
    if let Err(e) = result {
        eprintln!("pcap-index: {e}");
        std::process::exit(1);
    }
}
