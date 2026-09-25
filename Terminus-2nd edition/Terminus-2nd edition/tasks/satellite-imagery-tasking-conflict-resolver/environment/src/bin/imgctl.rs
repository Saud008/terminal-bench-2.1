use clap::Parser;
use satimg_tasking::wx_plan_seal::build_manifest;
use satimg_tasking::wx_pair_journal::write_plan_buffer;
use satimg_tasking::wx_schedule_core::resolve_plan;
use satimg_tasking::scenario_bind::write_scenario_bind;
use satimg_tasking::scenario_loader::read_scenario;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "imgctl", about = "Satellite imagery tasking conflict resolver")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(clap::Subcommand)]
enum Command {
    Resolve {
        #[arg(long)]
        scenario: String,
        #[arg(long)]
        token: String,
        #[arg(long)]
        dest: PathBuf,
    },
}

fn fixture_root() -> PathBuf {
    std::env::var("SAT_FIXTURE_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(satimg_tasking::DEFAULT_FIXTURE_ROOT))
}

fn load_scenario(name: &str) -> satimg_tasking::tasking_types::ScenarioBundle {
    let path = fixture_root().join(name).join("scenario.json");
    read_scenario(&path).expect("read scenario")
}

fn main() {
    let cli = Cli::parse();
    match cli.command {
        Command::Resolve { scenario, token, dest } => {
            let bundle = load_scenario(&scenario);
            fs::create_dir_all(satimg_tasking::VAR_ROOT).unwrap();
            write_scenario_bind(&token, &bundle).expect("scenario bind");
            let (mut assignments, preemptions) = resolve_plan(&bundle);
            write_plan_buffer(&token, &mut assignments).expect("plan buffer");
            let manifest = build_manifest(
                &token,
                &bundle.scenario_id,
                &bundle.constellation_id,
                assignments,
                preemptions,
            );
            fs::write(dest, serde_json::to_string_pretty(&manifest).unwrap()).unwrap();
        }
    }
}
