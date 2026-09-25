use component_gov::{DEFAULT_EXPORT_PATH, DEFAULT_LEDGER_PATH};

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
        "load" => {
            if args.len() != 3 {
                eprintln!("usage: component-gov load <components-dir>");
                return Err(2);
            }
            component_gov::load::load_directory(&args[2], DEFAULT_LEDGER_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "attest" => {
            if args.len() != 3 || args[2] != "export" {
                eprintln!("usage: component-gov attest export");
                return Err(2);
            }
            component_gov::export::attest_export(DEFAULT_LEDGER_PATH, DEFAULT_EXPORT_PATH)
                .map_err(|e| {
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
    eprintln!("usage: component-gov load <components-dir> | component-gov attest export");
}
