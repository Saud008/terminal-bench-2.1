use sled_engine::commit::state::commit_table;
use sled_engine::compaction::compact_table;
use sled_engine::export::{export_range, export_table};
use sled_engine::ingest::apply_batch_file;
use sled_engine::journal::crash_replay::replay_crash_journal;
use sled_engine::snapshot::pin_snapshot;
use sled_engine::staging::delete_key;
use sled_engine::walk::walk_table;
use std::path::PathBuf;

use clap::Parser;

#[derive(Debug, Parser)]
#[command(name = "sledtool")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Parser)]
enum Command {
    /// Apply JSONL put/delete ops to the staging table.
    Batch {
        #[arg(long)]
        table: String,
        #[arg(long)]
        input: PathBuf,
    },
    Delete {
        #[arg(long)]
        table: String,
        #[arg(long)]
        key: String,
    },
    /// Publish staging into committed storage and write sled-staging-snapshot.json.
    Publish {
        #[arg(long)]
        table: String,
    },
    /// Pin open snapshot page ids so compaction must not reclaim them.
    SnapshotPin {
        #[arg(long)]
        table: String,
        #[arg(long)]
        snapshot_id: String,
    },
    /// Reclaim unreachable pages not referenced by the live tree.
    Compact {
        #[arg(long)]
        table: String,
    },
    /// Replay a crash-boundary split journal without duplicating split markers.
    JournalReplay {
        #[arg(long)]
        table: String,
        #[arg(long)]
        journal: PathBuf,
    },
    /// Export committed keys in inclusive [start, end] range.
    ScanRange {
        #[arg(long)]
        table: String,
        #[arg(long)]
        start: String,
        #[arg(long)]
        end: String,
        #[arg(long)]
        out: PathBuf,
    },
    Export {
        #[arg(long)]
        table: String,
        #[arg(long)]
        out: PathBuf,
    },
    Walk {
        #[arg(long)]
        table: String,
    },
}

fn resolve_table(table: &str) -> String {
    if let Ok(prefix) = std::env::var("TB3_TABLE_PREFIX") {
        if prefix.starts_with('/') {
            return format!("{}/{}", prefix.trim_end_matches('/'), table);
        }
    }
    table.to_string()
}

fn main() -> Result<(), String> {
    let cli = Cli::parse();
    match cli.command {
        Command::Batch { table, input } => apply_batch_file(&resolve_table(&table), &input),
        Command::Delete { table, key } => delete_key(&resolve_table(&table), &key),
        Command::Publish { table } => commit_table(&resolve_table(&table)),
        Command::SnapshotPin {
            table,
            snapshot_id,
        } => pin_snapshot(&resolve_table(&table), &snapshot_id),
        Command::Compact { table } => {
            let freed = compact_table(&resolve_table(&table))?;
            println!("{{\"pages_freed\":{freed}}}");
            Ok(())
        }
        Command::JournalReplay { table, journal } => {
            let applied = replay_crash_journal(&resolve_table(&table), &journal)?;
            println!("{{\"entries_applied\":{applied}}}");
            Ok(())
        }
        Command::ScanRange {
            table,
            start,
            end,
            out,
        } => export_range(&resolve_table(&table), &start, &end, &out),
        Command::Export { table, out } => export_table(&resolve_table(&table), &out),
        Command::Walk { table } => {
            let report = walk_table(&resolve_table(&table))?;
            println!("{}", serde_json::to_string(&report).map_err(|e| e.to_string())?);
            Ok(())
        }
    }
}
