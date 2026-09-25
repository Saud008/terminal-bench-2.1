use clap::Parser;
use fishery_quota_map::bind_manifest;
use fishery_quota_map::jsonl_harvest;
use fishery_quota_map::models::SeasonPack;
use fishery_quota_map::quota_atlas;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "fqrctl", about = "Fishery quota landing reconciliation atlas emitter")]
struct Cli {
    /// Season fixture name under FQR_FIXTURE_ROOT
    #[arg(long)]
    season: String,
    /// Run token for /app/var artifacts
    #[arg(long)]
    token: String,
    /// Quota atlas JSON destination
    #[arg(long)]
    dest: PathBuf,
}

fn fixture_root() -> PathBuf {
    std::env::var("FQR_FIXTURE_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(fishery_quota_map::DEFAULT_FIXTURE_ROOT))
}

fn main() {
    let cli = Cli::parse();
    let path = fixture_root().join(&cli.season).join("season.json");
    let pack = bind_manifest::read_season_pack(&path).expect("read season pack");
    fs::create_dir_all(fishery_quota_map::VAR_ROOT).unwrap();
    fs::write(
        bind_manifest::bind_path(&cli.token),
        serde_json::to_string_pretty(&pack).unwrap(),
    )
    .unwrap();
    let (_header, rows) =
        jsonl_harvest::write_jsonl_ledger(&cli.token, &pack).expect("write jsonl ledger");
    let atlas = quota_atlas::build_quota_atlas(&cli.token, &pack, &rows);
    fs::write(cli.dest, serde_json::to_string_pretty(&atlas).unwrap()).unwrap();
}
