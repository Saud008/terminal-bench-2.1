#!/usr/bin/env python3
"""Bootstrap git-packfile-delta-chain-base-offset-closure-atlas task tree."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = REPO / "tasks" / "git-packfile-delta-chain-base-offset-closure-atlas"
ENV = TASK / "environment"
RUST_SHA = "9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36"


def wrel(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def main() -> None:
    if TASK.is_dir():
        shutil.rmtree(TASK)
    for sub in (
        "environment/src/ingest",
        "environment/src/normalize",
        "environment/src/staging",
        "environment/src/export",
        "environment/src/state",
        "environment/src/schema/_legacy",
        "environment/docs",
        "environment/scripts",
        "environment/tools",
        "tests/patches/ingest",
        "tests/patches/normalize",
        "tests/patches/staging",
        "tests/patches/export",
        "tests/patches/state",
        "tests/broken_src/src/ingest",
        "tests/broken_src/src/normalize",
        "tests/broken_src/src/staging",
        "tests/broken_src/src/export",
        "tests/broken_src/src/state",
        "solution/patches/ingest",
        "solution/patches/normalize",
        "solution/patches/staging",
        "solution/patches/export",
        "solution/patches/state",
    ):
        (TASK / sub).mkdir(parents=True, exist_ok=True)

    wrel(
        TASK,
        "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "build-and-dependency-management"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["rust", "bash"]
tags = ["git", "packfile", "delta-chain", "closure", "oid", "rust-cli", "vcs"]
expert_time_estimate_min = 260
junior_time_estimate_min = 540

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900.0
cpus = 2
memory_mb = 4096
storage_mb = 10240
""",
    )

    wrel(
        TASK,
        "instruction.md",
        """Build the packfold Git packfile delta-chain closure CLI at /usr/local/bin/packfold and complete the Rust sources under /app/. The tool decodes JSONL pack index shards from /app/fixtures/pack/, persists a pack closure atlas at /app/state/pack-closure-atlas.json, and emits a sealed pack verification manifest to /app/output/sealed-pack-manifest.json.

Behavioral contracts live in /app/docs/pack-entry-schema.md, /app/docs/object-type-coalesce.md, /app/docs/closure-atlas-schema.md, /app/docs/sealed-pack-manifest-schema.md, /app/docs/cli-surface.md, /app/docs/fixture-catalog.md, and /app/docs/module-api.md. Bundled fixtures are under /app/fixtures/pack/. When TB3_FIXTURES_DIR points at an absolute directory under /opt/verifier-fixtures/pack/, the same resolve-seal pipeline must handle those hidden fixtures with matching atlas digests and manifest checksums.

The CLI must quarantine missing or corrupt JSONL with exit 1. Missing required flags exit 2. Seal must read only the pack closure atlas and must not reopen pack shard files. Rebuild with cargo build --release --locked -o /usr/local/bin/packfold after source edits. Do not run apt-get, pip install, or other network installs.

Do not edit /app/docs/, /app/fixtures/, or /app/tools/.
""",
    )

    wrel(
        ENV,
        "Dockerfile",
        f"""FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:{RUST_SHA}

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash ca-certificates tmux asciinema python3 python3-venv \\
    && rm -rf /var/lib/apt/lists/* \\
    && python3 -m venv /opt/verifier-venv \\
    && /opt/verifier-venv/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${{PATH}}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src/ ./src/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY tools/ ./tools/

RUN mkdir -p /app/fixtures/pack /app/state /app/output /opt/verifier-fixtures/pack \\
        /opt/verifier-broken-packfold-src \\
    && find /app/scripts /app/tools -name '*.py' -exec sed -i 's/\\r$//' {{}} + \\
    && find /app/scripts -name '*.sh' -exec sed -i 's/\\r$//' {{}} + \\
    && chmod +x /app/scripts/*.sh /app/tools/*.py \\
    && python3 /app/tools/build_fixtures.py /app/fixtures/pack \\
    && python3 /app/tools/build_hidden_fixtures.py /opt/verifier-fixtures/pack \\
    && cp -a /app/src/. /opt/verifier-broken-packfold-src/src/ \\
    && cargo build --release --locked \\
    && install -m 0755 target/release/packfold /usr/local/bin/packfold
""",
    )

    wrel(ENV, ".dockerignore", "target/\n**/__pycache__/\n")

    wrel(
        ENV,
        "Cargo.toml",
        """[package]
name = "packfold"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "packfold"
path = "src/main.rs"

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
sha2 = "0.10"
""",
    )

    # Generate lock file via cargo later; placeholder minimal lock
    wrel(ENV, "Cargo.lock", "")

    # Shared Rust sources written by helper
    write_rust_sources(ENV / "src", broken=True)
    write_docs(ENV / "docs")
    write_tools(ENV / "tools")
    write_scripts(ENV / "scripts")
    write_tests(TASK)
    write_solution(TASK)

    # Copy broken to tests/broken_src, fixed to patches
    copy_tree(ENV / "src", TASK / "tests" / "broken_src" / "src")
    for mod, fname in MODULES:
        fixed = read_module_source(broken=False, mod=mod, fname=fname)
        for dest in (
            TASK / "tests" / "patches" / mod / fname,
            TASK / "solution" / "patches" / mod / fname,
        ):
            wrel(dest.parent.parent.parent, str(dest.relative_to(dest.parent.parent.parent)), fixed)

    print(f"Bootstrapped {TASK}")


MODULES = [
    ("ingest", "pack_entry_reader.rs"),
    ("normalize", "object_type_coalesce.rs"),
    ("staging", "closure_watermark.rs"),
    ("export", "pack_seal.rs"),
    ("state", "resume_chain_gate.rs"),
]


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def write_rust_sources(src_root: Path, *, broken: bool) -> None:
    for mod, fname in MODULES:
        content = read_module_source(broken=broken, mod=mod, fname=fname)
        wrel(src_root.parent, f"src/{mod}/{fname}", content)
    for rel, content in BASE_RUST.items():
        wrel(src_root.parent, f"src/{rel}", content)
    wrel(
        src_root.parent,
        "src/schema/_legacy/deflate_window_resolver.rs",
        DECOY_RS,
    )


def read_module_source(*, broken: bool, mod: str, fname: str) -> str:
    key = f"{mod}/{fname}"
    return BROKEN_MODULES[key] if broken else FIXED_MODULES[key]


BASE_RUST = {}
DECOY_RS = ""


def write_docs(docs: Path) -> None:
    for name, body in DOCS.items():
        wrel(docs.parent, f"docs/{name}", body)


def write_tools(tools: Path) -> None:
    wrel(tools.parent, "tools/build_fixtures.py", BUILD_FIXTURES)
    wrel(tools.parent, "tools/build_hidden_fixtures.py", BUILD_HIDDEN)


def write_scripts(scripts: Path) -> None:
    wrel(scripts.parent, "scripts/reset-state.sh", RESET_SH)


def write_tests(task: Path) -> None:
    wrel(task, "tests/test.sh", TEST_SH)
    wrel(task, "tests/reference_packfold.py", REFERENCE_PY)
    wrel(task, "tests/test_outputs.py", TEST_OUTPUTS)


def write_solution(task: Path) -> None:
    wrel(task, "solution/solve.sh", SOLVE_SH)


# --- content blocks appended below via exec in same file ---

if __name__ == "__main__":
    exec(open(__file__, encoding="utf-8").read().split("# --- content blocks")[1])
    main()
