use std::path::PathBuf;

use agerecv::admit::corpus_walk;
use agerecv::policy::pin_set;
use agerecv::seal::{ledger_emit, witness_stage};

fn next_arg(args: &[String], i: &mut usize, flag: &str) -> PathBuf {
    *i += 1;
    let val = args.get(*i).unwrap_or_else(|| {
        eprintln!("missing value for {flag}");
        std::process::exit(1);
    });
    PathBuf::from(val)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: agerecv <stage-witness|seal-ledger> [--flags]");
        std::process::exit(1);
    }

    match args[1].as_str() {
        "stage-witness" => {
            let mut corpus: Option<PathBuf> = None;
            let mut policy: Option<PathBuf> = None;
            let mut witness: Option<PathBuf> = None;
            let mut i = 2;
            while i < args.len() {
                match args[i].as_str() {
                    "--corpus" => corpus = Some(next_arg(&args, &mut i, "--corpus")),
                    "--policy" => policy = Some(next_arg(&args, &mut i, "--policy")),
                    "--witness" => witness = Some(next_arg(&args, &mut i, "--witness")),
                    other => {
                        eprintln!("unknown flag: {other}");
                        std::process::exit(1);
                    }
                }
                i += 1;
            }
            let corpus = corpus.unwrap_or_else(|| {
                eprintln!("--corpus is required");
                std::process::exit(1);
            });
            let policy_path = policy.unwrap_or_else(|| {
                eprintln!("--policy is required");
                std::process::exit(1);
            });
            let witness = witness.unwrap_or_else(|| {
                eprintln!("--witness is required");
                std::process::exit(1);
            });

            let _policy = pin_set::load_policy(&policy_path).expect("policy");
            let corpus_dir = std::env::var("AGE_CORPUS_DIR")
                .map(PathBuf::from)
                .unwrap_or(corpus);
            let files = corpus_walk::walk_corpus(&corpus_dir).expect("corpus");
            witness_stage::write_witness(&witness, &files).expect("witness");
        }
        "seal-ledger" => {
            let mut witness: Option<PathBuf> = None;
            let mut policy: Option<PathBuf> = None;
            let mut out: Option<PathBuf> = None;
            let mut i = 2;
            while i < args.len() {
                match args[i].as_str() {
                    "--witness" => witness = Some(next_arg(&args, &mut i, "--witness")),
                    "--policy" => policy = Some(next_arg(&args, &mut i, "--policy")),
                    "--out" => out = Some(next_arg(&args, &mut i, "--out")),
                    other => {
                        eprintln!("unknown flag: {other}");
                        std::process::exit(1);
                    }
                }
                i += 1;
            }
            let witness = witness.unwrap_or_else(|| {
                eprintln!("--witness is required");
                std::process::exit(1);
            });
            let policy_path = policy.unwrap_or_else(|| {
                eprintln!("--policy is required");
                std::process::exit(1);
            });
            let out = out.unwrap_or_else(|| {
                eprintln!("--out is required");
                std::process::exit(1);
            });

            let policy = pin_set::load_policy(&policy_path).expect("policy");
            let files = witness_stage::read_witness(&witness).expect("witness");
            ledger_emit::seal_ledger(&out, &files, &policy).expect("ledger");
        }
        other => {
            eprintln!("unknown command: {other}");
            std::process::exit(1);
        }
    }
}
