use clap::{Parser, Subcommand};
use aissegment::{run_atlas_emit, run_stream_feed};

#[derive(Parser, Debug)]
#[command(name = "aissegment", about = "AIS voyage leg anomaly segmenter")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Normalize an AIS JSONL stream into a track snapshot.
    Feed {
        #[arg(long)]
        input: String,
        #[arg(long, default_value = "/app/state/track-snapshot.json")]
        snapshot: String,
        #[arg(long, default_value = "/app/fixtures/ports.geojson")]
        ports: String,
    },
    /// Emit voyage-atlas.json from a track snapshot.
    Atlas {
        #[arg(long, default_value = "/app/output/voyage-atlas.json")]
        output: String,
        #[arg(long, default_value = "/app/state/track-snapshot.json")]
        snapshot: String,
        #[arg(long, default_value = "/app/fixtures/ports.geojson")]
        ports: String,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Feed {
            input,
            snapshot,
            ports,
        } => match run_stream_feed(&input, &snapshot, &ports) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("{e}");
                2
            }
        },
        Commands::Atlas {
            output,
            snapshot,
            ports,
        } => match run_atlas_emit(&snapshot, &output, &ports) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("{e}");
                2
            }
        },
    };
    std::process::exit(code);
}
