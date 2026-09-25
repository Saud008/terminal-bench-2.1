use std::fs;
use std::path::PathBuf;

use clap::Parser;
use mav_core::{decode_stream, publish_from_snapshot, DecodeOptions};

#[derive(Parser)]
#[command(name = "mavctl")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(clap::Subcommand)]
enum Commands {
    Decode {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        seed: String,
        #[arg(long)]
        export: PathBuf,
        #[arg(long)]
        checkpoint: Option<PathBuf>,
        #[arg(long, default_value_t = false)]
        resume: bool,
    },
    Publish {
        #[arg(long)]
        export: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Decode {
            input,
            seed,
            export,
            checkpoint,
            resume,
        } => run_decode(&input, &seed, &export, checkpoint.as_deref(), resume),
        Commands::Publish { export } => run_publish(&export),
    };
    std::process::exit(code);
}

fn run_decode(
    input: &PathBuf,
    seed: &str,
    export: &PathBuf,
    checkpoint: Option<&std::path::Path>,
    resume: bool,
) -> i32 {
    let bytes = match fs::read(input) {
        Ok(data) => data,
        Err(err) => {
            eprintln!("{err}");
            return 1;
        }
    };
    let opts = DecodeOptions {
        seed,
        checkpoint,
        resume,
    };
    match decode_stream(&bytes, &opts) {
        Ok(doc) => write_json(export, &doc).map(|_| 0).unwrap_or(1),
        Err(err) => {
            eprintln!("{err}");
            1
        }
    }
}

fn run_publish(export: &PathBuf) -> i32 {
    match publish_from_snapshot() {
        Ok(doc) => write_json(export, &doc).map(|_| 0).unwrap_or(1),
        Err(err) => {
            eprintln!("{err}");
            1
        }
    }
}

fn write_json(path: &PathBuf, doc: &mav_core::ExportDoc) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let json = serde_json::to_string_pretty(doc).expect("serialize");
    fs::write(path, format!("{json}\n"))
}
