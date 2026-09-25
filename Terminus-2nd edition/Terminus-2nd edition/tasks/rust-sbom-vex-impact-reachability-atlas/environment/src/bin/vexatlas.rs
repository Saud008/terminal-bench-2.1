use vexatlas::DEFAULT_SNAPSHOT_PATH;

fn main() {
    if let Err(code) = run() {
        std::process::exit(code);
    }
}

fn run() -> Result<(), i32> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        usage();
        return Err(2);
    }
    match args[1].as_str() {
        "capture" => {
            if args.len() != 4 || args[2] != "--bundle" {
                eprintln!("usage: vexatlas capture --bundle <bundle.json>");
                return Err(2);
            }
            vexatlas::bundlecap::capture_bundle(&args[3], DEFAULT_SNAPSHOT_PATH).map_err(|e| {
                eprintln!("{e}");
                if e.contains("read bundle") {
                    2
                } else {
                    1
                }
            })?;
        }
        "rollup" => {
            if args.len() != 4 || args[2] != "--output" {
                eprintln!("usage: vexatlas rollup --output <path>");
                return Err(2);
            }
            if !std::path::Path::new(DEFAULT_SNAPSHOT_PATH).exists() {
                eprintln!("rollup before capture");
                return Err(3);
            }
            vexatlas::rptgen::rollup::export_atlas(DEFAULT_SNAPSHOT_PATH, &args[3]).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        _ => {
            usage();
            return Err(2);
        }
    }
    Ok(())
}

fn usage() {
    eprintln!("usage: vexatlas capture --bundle <bundle.json> | vexatlas rollup --output <path>");
}
