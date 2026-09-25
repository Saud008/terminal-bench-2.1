use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "jscovmap")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Trace {
        #[arg(long)]
        schema_dir: PathBuf,
        #[arg(long)]
        examples: PathBuf,
        #[arg(long)]
        ref_edges: PathBuf,
        #[arg(long)]
        coverage: PathBuf,
    },
    Publish {
        #[arg(long)]
        ref_edges: PathBuf,
        #[arg(long)]
        coverage: PathBuf,
        #[arg(long)]
        report: PathBuf,
        #[arg(long)]
        graph: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Trace {
            schema_dir,
            examples,
            ref_edges,
            coverage,
        } => match staging_write::trace(&schema_dir, &examples, &ref_edges, &coverage) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("trace error: {e}");
                1
            }
        },
        Commands::Publish {
            ref_edges,
            coverage,
            report,
            graph,
        } => match report_emit::publish_all(&ref_edges, &coverage, &report, &graph) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("publish error: {e}");
                1
            }
        },
    };
    std::process::exit(code);
}
