#!/usr/bin/env python3
"""Migrate task Dockerfiles to Snorkel ECR canonical base images (canonical-base-image-gate.mdc).

Usage:
  # Check one task
  python3 scripts/migrate_dockerfile_canonical_ecr.py --check --task-dir tasks/<name>

  # Auto-fix known legacy images (tasks/ + tasksss/ + dusre-wale/)
  python3 scripts/migrate_dockerfile_canonical_ecr.py

  # Fix + verify one task (pack_zip.sh runs this automatically)
  python3 scripts/migrate_dockerfile_canonical_ecr.py --ensure --task-dir tasks/<name>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_ROOTS = (
    REPO_ROOT / "tasks",
    REPO_ROOT / "tasksss",
    REPO_ROOT / "dusre-wale",
)

ECR_PREFIX = "public.ecr.aws/docker/library/"
# TB2 platform canonical Go/Rust bases (check_canonical_base_images.yaml)
TBENCH_PREFIX = "ghcr.io/laude-institute/t-bench/"
SANCTIONED_FROM_PREFIXES = (ECR_PREFIX, TBENCH_PREFIX)

# Old image@digest substring -> ECR canonical (order: longer/more specific first)
REPLACEMENTS: list[tuple[str, str]] = [
    (
        "golang:1.22.12-bookworm@sha256:1f298b0c9fecdf504389a0329236f948cc04a566a2bb32337207cbaaa2f8177c",
        "public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac",
    ),
    (
        "golang:1.22.12-bookworm@sha256:3d699e4d15d0f8f13c9195c0632a16702b8cbdece2955af1c23b37ae5d55a253",
        "public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac",
    ),
    (
        "rust:1.85.0-slim-bookworm@sha256:c842cc0357b91bb15ad2bb89934513d0d226f711fac7f7fedb176d3311714d47",
        "public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36",
    ),
    (
        "rust:1.84.1-bookworm@sha256:479476fa1dec14dfa9ed2dbcaa94cda5ab945e125d45c2d153267cc0135f3b69",
        "public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36",
    ),
    (
        "rust:1.82-bookworm@sha256:d9c3c6f1264a547d84560e06ffd79ed7a799ce0bff0980b26cf10d29af888377",
        "public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36",
    ),
    (
        "rust:1.78-bookworm@sha256:653bd24b9a8f9800c67df55fea5637a97152153fd744a4ef78dd41f7ddc40144",
        "public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36",
    ),
    (
        "node:20.18.1-bookworm-slim@sha256:35eccf0e5cdb40b8ba3531e1b756d0ed52ec6e9d74c1756cc6503e8734effd27",
        "public.ecr.aws/docker/library/node:22-bookworm-slim@sha256:f3a68cf41a855d227d1b0ab832bed9749469ef38cf4f58182fb8c893bc462383",
    ),
    (
        "debian:bookworm-slim@sha256:0104b334637a5f19aa9c983a91b54c89887c0984081f2068983107a6f6c21eeb",
        "public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d",
    ),
    (
        "python:3.12-slim-bookworm@sha256:93ab4b7fa528b25124c97bcc755415e60eb671a86b4dbe0328df2fe2d1c1193d",
        "public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb",
    ),
    (
        "python:3.11-slim-bookworm@sha256:8e0cfa63b1dff7ed3650ce020cffd42b46783a0d510cd9240a83d12920336ccc",
        "public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb",
    ),
    (
        "ruby:3.3.6-slim-bookworm@sha256:b210597cc7d05e19edf9c8e7935dcf1554886905dcdad0475cfe63a654147f7a",
        "public.ecr.aws/docker/library/ruby:3.3-slim-bookworm@sha256:e76733e94b3a5893e4a141024ef3a583dc10781dc24becebf74f9c9f9a33e3df",
    ),
    (
        "eclipse-temurin:17-jdk-jammy@sha256:beabb759e6f9653c843958d1d1f5cecb881dfb85aa6081e2bef099ab1260344e",
        "public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14",
    ),
]


def ensure_canonical_task(task_dir: Path, *, quiet: bool = False) -> int:
    """Auto-fix known legacy FROM patterns, then verify all stages use ECR/t-bench.

    Used before harbor build, audit, and finish — not only at pack_zip.
    Returns 0 when every FROM is sanctioned; 1 otherwise.
    """
    resolved = resolve_task_dir(task_dir)
    dockerfiles = discover_dockerfiles(resolved)
    if not dockerfiles:
        if not quiet:
            print(f"No environment/Dockerfile under {resolved}", file=sys.stderr)
        return 1
    run_migrate(dockerfiles, quiet=quiet)
    return run_check(dockerfiles, quiet=quiet)


def resolve_task_dir(path: Path) -> Path:
    p = path.expanduser()
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def discover_dockerfiles(task_dir: Path | None = None) -> list[Path]:
    if task_dir is not None:
        df = task_dir / "environment" / "Dockerfile"
        return [df] if df.is_file() else []
    out: list[Path] = []
    for root in TASK_ROOTS:
        if root.is_dir():
            out.extend(sorted(root.glob("**/environment/Dockerfile")))
    return out


def migrate_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def _from_is_sanctioned(line: str) -> bool:
    if not line.startswith("FROM "):
        return True
    return any(prefix in line for prefix in SANCTIONED_FROM_PREFIXES)


def non_ecr_from_lines(dockerfiles: list[Path]) -> list[str]:
    remaining: list[str] = []
    for df in dockerfiles:
        for i, line in enumerate(df.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("FROM ") and not _from_is_sanctioned(line):
                remaining.append(f"{df.relative_to(REPO_ROOT)}:{i}:{line.strip()}")
    return remaining


def run_check(dockerfiles: list[Path], quiet: bool = False) -> int:
    remaining = non_ecr_from_lines(dockerfiles)
    if remaining:
        if not quiet:
            print(f"Non-canonical FROM lines ({len(remaining)}):", file=sys.stderr)
            for r in remaining:
                print(f"  {r}", file=sys.stderr)
            print(
                "\nFix known patterns: python3 scripts/migrate_dockerfile_canonical_ecr.py "
                "[--task-dir tasks/<name>]",
                file=sys.stderr,
            )
        return 1
    if not quiet:
        print(f"OK: {len(dockerfiles)} Dockerfile(s) use Snorkel ECR canonical images.")
    return 0


def run_migrate(dockerfiles: list[Path], quiet: bool = False) -> list[Path]:
    changed: list[Path] = []
    for df in dockerfiles:
        if migrate_file(df):
            changed.append(df.relative_to(REPO_ROOT))
    if changed and not quiet:
        print(f"Canonical ECR: updated {len(changed)} Dockerfile(s)")
        for p in changed:
            print(f"  {p}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Snorkel ECR canonical FROM — check, fix, or ensure before zip.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only; exit 1 if any FROM lacks public.ecr.aws/docker/library/",
    )
    parser.add_argument(
        "--ensure",
        action="store_true",
        help="Auto-fix known legacy images, then verify (pack_zip.sh uses this)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors / summary on failure",
    )
    parser.add_argument(
        "--task-dir",
        type=Path,
        help="Single task directory (e.g. tasks/foo, tasksss/foo)",
    )
    args = parser.parse_args()

    if args.check and args.ensure:
        print("Use --check or --ensure, not both.", file=sys.stderr)
        return 2

    task_dir = resolve_task_dir(args.task_dir) if args.task_dir else None
    dockerfiles = discover_dockerfiles(task_dir)
    if not dockerfiles:
        print("No environment/Dockerfile found.", file=sys.stderr)
        return 1

    if args.check:
        return run_check(dockerfiles, quiet=args.quiet)

    if args.ensure:
        run_migrate(dockerfiles, quiet=args.quiet)
        return run_check(dockerfiles, quiet=args.quiet)

    changed = run_migrate(dockerfiles, quiet=args.quiet)
    if not changed:
        scope = "Dockerfile(s)" if args.task_dir else "Dockerfiles"
        if not args.quiet:
            print(f"Scanned {len(dockerfiles)} {scope} — no known legacy patterns to replace.")

    rc = run_check(dockerfiles, quiet=args.quiet)
    if rc == 0 and not args.quiet and not args.task_dir:
        print(f"\nAll {len(dockerfiles)} Dockerfile(s) use public.ecr.aws canonical images.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
