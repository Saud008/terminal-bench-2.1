use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "mdtable")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Export {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        export: PathBuf,
        #[arg(long, default_value = "json")]
        format: String,
    },
    Publish {
        #[arg(long)]
        export: PathBuf,
        #[arg(long, default_value = "json")]
        format: String,
    },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Export {
            input,
            export,
            format,
        } => match format.as_str() {
            "json" => {
                mdtable_core::export_json(&input, &export)?;
            }
            "html" => {
                mdtable_core::export_html(&input, &export)?;
            }
            other => anyhow::bail!("unknown format: {other}"),
        },
        Commands::Publish { export, format } => match format.as_str() {
            "json" => {
                mdtable_core::publish_json(&export)?;
            }
            "html" => {
                mdtable_core::publish_html(&export)?;
            }
            other => anyhow::bail!("unknown format: {other}"),
        },
    }
    Ok(())
}
