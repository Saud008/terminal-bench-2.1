use peg_audit::{
    DEFAULT_AUDIT_PATH, DEFAULT_CHECKSUM_PATH, DEFAULT_GRAPH_PATH, DEFAULT_PARSE_PATH,
};

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
                eprintln!("usage: pestctl ingest <grammars-dir>");
                return Err(2);
            }
            peg_audit::ingest::ingest_directory(&args[2], DEFAULT_GRAPH_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "climb" => {
            if args.len() < 3 || args[2] != "parse" {
                eprintln!("usage: pestctl climb parse --input <tokens-json> [--graph <path>]");
                return Err(2);
            }
            let mut input = String::new();
            let mut graph = DEFAULT_GRAPH_PATH.to_string();
            let mut i = 3;
            while i < args.len() {
                match args[i].as_str() {
                    "--input" if i + 1 < args.len() => {
                        input = args[i + 1].clone();
                        i += 2;
                    }
                    "--graph" if i + 1 < args.len() => {
                        graph = args[i + 1].clone();
                        i += 2;
                    }
                    _ => {
                        eprintln!("usage: pestctl climb parse --input <tokens-json> [--graph <path>]");
                        return Err(2);
                    }
                }
            }
            if input.is_empty() {
                eprintln!("climb parse: --input required");
                return Err(2);
            }
            peg_audit::climb::run_parse(&graph, &input, DEFAULT_PARSE_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "audit" => {
            if args.len() != 3 || args[2] != "export" {
                eprintln!("usage: pestctl audit export");
                return Err(2);
            }
            peg_audit::export::audit_export(
                DEFAULT_GRAPH_PATH,
                DEFAULT_PARSE_PATH,
                DEFAULT_AUDIT_PATH,
                DEFAULT_CHECKSUM_PATH,
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
    eprintln!("usage: pestctl ingest <dir> | pestctl climb parse --input <json> | pestctl audit export");
}
