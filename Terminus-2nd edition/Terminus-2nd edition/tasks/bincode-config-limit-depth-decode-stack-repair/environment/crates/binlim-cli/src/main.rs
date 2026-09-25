use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

use anyhow::{Context, Result};
use binlim_core::decode_payload;
use clap::Parser;
use serde_json;

#[derive(Parser, Debug)]
#[command(name = "binlim")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(clap::Subcommand, Debug)]
enum Commands {
    Decode {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        max_depth: u32,
        #[arg(long)]
        max_bytes: u64,
    },
}

fn main() -> Result<ExitCode> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Decode {
            input,
            output,
            max_depth,
            max_bytes,
        } => {
            let data = fs::read(&input).with_context(|| format!("read {}", input.display()))?;
            let report = decode_payload(&data, max_depth, max_bytes);
            let code = exit_for_report(&report);
            let json = serde_json::to_string_pretty(&report)?;
            if let Some(parent) = output.parent() {
                if !parent.as_os_str().is_empty() {
                    fs::create_dir_all(parent)?;
                }
            }
            fs::write(&output, json)?;
            Ok(code)
        }
    }
}

fn exit_for_report(report: &binlim_core::DecodeReport) -> ExitCode {
    if report.status == "ok" {
        return ExitCode::from(0);
    }
    match report.error_code {
        Some("limit_exceeded") => ExitCode::from(2),
        Some("invalid_varint") | Some("invalid_tag") => ExitCode::from(3),
        _ => ExitCode::from(4),
    }
}
