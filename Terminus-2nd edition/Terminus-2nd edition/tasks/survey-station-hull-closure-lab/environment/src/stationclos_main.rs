use std::env;
use std::path::PathBuf;
use std::process;

fn usage() -> ! {
    eprintln!("usage: stationclos materialize-hulls --campaign <cid> --bundle <name>");
    eprintln!("       stationclos certify-campaign --campaign <cid> --output <path>");
    process::exit(2);
}

fn main() {
    let mut args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() {
        usage();
    }
    let cmd = args.remove(0);
    match cmd.as_str() {
        "materialize-hulls" => {
            let mut campaign = None;
            let mut bundle = None;
            let mut i = 0;
            while i < args.len() {
                match args[i].as_str() {
                    "--campaign" => {
                        i += 1;
                        campaign = args.get(i).cloned();
                    }
                    "--bundle" => {
                        i += 1;
                        bundle = args.get(i).cloned();
                    }
                    _ => usage(),
                }
                i += 1;
            }
            let campaign = campaign.unwrap_or_else(|| usage());
            let bundle = bundle.unwrap_or_else(|| usage());
            if let Err(e) = survey_triangulation_residual_closure::materialize_hulls(&campaign, &bundle) {
                eprintln!("{e}");
                process::exit(1);
            }
        }
        "certify-campaign" => {
            let mut campaign = None;
            let mut output = None;
            let mut i = 0;
            while i < args.len() {
                match args[i].as_str() {
                    "--campaign" => {
                        i += 1;
                        campaign = args.get(i).cloned();
                    }
                    "--output" => {
                        i += 1;
                        output = args.get(i).cloned();
                    }
                    _ => usage(),
                }
                i += 1;
            }
            let campaign = campaign.unwrap_or_else(|| usage());
            let output = PathBuf::from(output.unwrap_or_else(|| usage()));
            if let Err(e) = survey_triangulation_residual_closure::certify_campaign(&campaign, &output) {
                eprintln!("{e}");
                process::exit(1);
            }
        }
        _ => usage(),
    }
}
