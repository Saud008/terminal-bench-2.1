use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;
use std::process::ExitCode;

#[derive(Parser, Debug)]
#[command(name = "fbdecode", about = "FlatBuffers scene JSON bundler")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Decode wire bytes, write snapshot, append ledger (no stdout JSON).
    Stage {
        #[arg(long)]
        schema: PathBuf,
        #[arg(long)]
        input: PathBuf,
    },
    /// Render staged snapshot JSON to stdout.
    Export {
        #[arg(long)]
        schema: PathBuf,
    },
    /// Report whether snapshot and ledger heads are aligned.
    Verify {
        #[arg(long)]
        schema: PathBuf,
    },
    /// Stage then export in one invocation.
    Decode {
        #[arg(long)]
        schema: PathBuf,
        #[arg(long)]
        input: PathBuf,
    },
}

fn run() -> Result<ExitCode> {
    let cli = match Cli::try_parse() {
        Ok(cli) => cli,
        Err(err) => {
            // Missing required flags / clap usage → exit 2
            let _ = err.print();
            return Ok(ExitCode::from(2));
        }
    };

    match cli.command {
        Commands::Stage { schema: _, input } => {
            let buf = std::fs::read(&input)?;
            fbpkg::rw14::stage_buffer(&buf)?;
            Ok(ExitCode::SUCCESS)
        }
        Commands::Export { schema: _ } => {
            let json = fbpkg::rw14::export_from_state()?;
            print!("{json}");
            Ok(ExitCode::SUCCESS)
        }
        Commands::Verify { schema: _ } => {
            let aligned = fbpkg::rw14::verify_state()?;
            let body = serde_json::json!({ "aligned": aligned });
            println!("{body}");
            if aligned {
                Ok(ExitCode::SUCCESS)
            } else {
                Ok(ExitCode::from(1))
            }
        }
        Commands::Decode { schema: _, input } => {
            let buf = std::fs::read(&input)?;
            let json = fbpkg::rw14::decode_buffer_json(&buf)?;
            print!("{json}");
            Ok(ExitCode::SUCCESS)
        }
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(code) => code,
        Err(err) => {
            eprintln!("{err:#}");
            ExitCode::from(1)
        }
    }
}
