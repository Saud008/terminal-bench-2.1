use tantool::commit::commit_index;
use tantool::export::search::search_index;
use tantool::ingest::batch::ingest_batch;
use tantool::merge::scheduler::merge_staging_segments;
use tantool::stats::stats_for_index;
use clap::Parser;
use std::path::PathBuf;

#[derive(Debug, Parser)]
#[command(name = "tantool")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Parser)]
enum Command {
    /// Ingest a JSONL batch into a new staging segment.
    Ingest {
        #[arg(long)]
        index: String,
        #[arg(long)]
        input: PathBuf,
    },
    /// Merge all staging segments into one committed segment.
    Merge {
        #[arg(long)]
        index: String,
    },
    /// Commit merged segments with WAL barrier and snapshot.
    Commit {
        #[arg(long)]
        index: String,
    },
    /// Search committed postings for a field term.
    Search {
        #[arg(long)]
        index: String,
        #[arg(long)]
        field: String,
        #[arg(long)]
        term: String,
        #[arg(long)]
        out: PathBuf,
    },
    /// Print index statistics as JSON on stdout.
    Stats {
        #[arg(long)]
        index: String,
    },
}

fn resolve_index(index: &str) -> String {
    if let Ok(prefix) = std::env::var("TB3_INDEX_PREFIX") {
        if prefix.starts_with('/') {
            return format!("{}/{}", prefix.trim_end_matches('/'), index);
        }
    }
    index.to_string()
}

fn main() -> Result<(), String> {
    let cli = Cli::parse();
    match cli.command {
        Command::Ingest { index, input } => {
            let name = resolve_index(&index);
            ingest_batch(&name, &input)?;
            Ok(())
        }
        Command::Merge { index } => {
            let name = resolve_index(&index);
            merge_staging_segments(&name)?;
            Ok(())
        }
        Command::Commit { index } => {
            let name = resolve_index(&index);
            commit_index(&name)?;
            Ok(())
        }
        Command::Search {
            index,
            field,
            term,
            out,
        } => {
            let name = resolve_index(&index);
            search_index(&name, &field, &term, &out)
        }
        Command::Stats { index } => {
            let name = resolve_index(&index);
            let report = stats_for_index(&name)?;
            println!(
                "{}",
                serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
            );
            Ok(())
        }
    }
}
