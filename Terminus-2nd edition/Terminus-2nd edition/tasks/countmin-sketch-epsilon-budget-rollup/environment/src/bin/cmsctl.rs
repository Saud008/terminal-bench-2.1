use cms_merge::DEFAULT_FIXTURE_ROOT;

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
        "ingest" => parse_seed_bundle(&args, 2, cms_merge::ingest::run_ingest),
        "merge" => parse_seed_bundle(&args, 2, cms_merge::merge::run_merge),
        "export" => parse_export(&args),
        _ => {
            usage();
            Err(2)
        }
    }
}

fn parse_seed_bundle<F>(args: &[String], start: usize, f: F) -> Result<(), i32>
where
    F: Fn(&str, &str, &str) -> Result<(), String>,
{
    let mut seed = String::new();
    let mut bundle = String::new();
    let mut fixture_dir = DEFAULT_FIXTURE_ROOT.to_string();
    let mut i = start;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--bundle" if i + 1 < args.len() => {
                bundle = args[i + 1].clone();
                i += 2;
            }
            "--fixture-dir" if i + 1 < args.len() => {
                fixture_dir = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if seed.is_empty() || bundle.is_empty() {
        eprintln!("--seed and --bundle required");
        return Err(2);
    }
    f(&seed, &bundle, &fixture_dir).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn parse_export(args: &[String]) -> Result<(), i32> {
    let mut seed = String::new();
    let mut bundle = String::new();
    let mut output = String::new();
    let mut fixture_dir = DEFAULT_FIXTURE_ROOT.to_string();
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].clone();
                i += 2;
            }
            "--bundle" if i + 1 < args.len() => {
                bundle = args[i + 1].clone();
                i += 2;
            }
            "--output" if i + 1 < args.len() => {
                output = args[i + 1].clone();
                i += 2;
            }
            "--fixture-dir" if i + 1 < args.len() => {
                fixture_dir = args[i + 1].clone();
                i += 2;
            }
            _ => {
                usage();
                return Err(2);
            }
        }
    }
    if seed.is_empty() || bundle.is_empty() || output.is_empty() {
        eprintln!("export requires --seed, --bundle, --output");
        return Err(2);
    }
    cms_merge::export::run_export(&seed, &bundle, &fixture_dir, &output).map_err(|e| {
        eprintln!("{e}");
        1
    })
}

fn usage() {
    eprintln!("cmsctl ingest --seed S --bundle B [--fixture-dir D]");
    eprintln!("cmsctl merge --seed S --bundle B [--fixture-dir D]");
    eprintln!("cmsctl export --seed S --bundle B --output P [--fixture-dir D]");
}
