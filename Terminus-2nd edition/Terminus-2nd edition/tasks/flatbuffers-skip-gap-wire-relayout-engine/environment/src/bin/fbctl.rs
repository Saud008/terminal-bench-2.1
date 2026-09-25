use fb_wire_relayout::{DEFAULT_LEDGER_PATH, DEFAULT_RELAYOUT_PATH, DEFAULT_SEAL_PATH};

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
        "ingest" => {
            if args.len() != 3 {
                eprintln!("usage: fbctl ingest <wires-dir>");
                return Err(2);
            }
            fb_wire_relayout::ingest::ingest_directory(&args[2], DEFAULT_LEDGER_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "relayout" => {
            if args.len() != 3 || args[2] != "export" {
                eprintln!("usage: fbctl relayout export");
                return Err(2);
            }
            fb_wire_relayout::export::relayout_export(
                DEFAULT_LEDGER_PATH,
                DEFAULT_RELAYOUT_PATH,
                DEFAULT_SEAL_PATH,
            )
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
    eprintln!("usage: fbctl ingest <wires-dir> | fbctl relayout export");
}
