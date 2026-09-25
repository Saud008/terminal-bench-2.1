#!/usr/bin/env python3
"""Fail if task.toml has undocumented / unsupported fields.

See .cursor/rules/shared/task-toml-supported-fields-only.mdc
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE = ".cursor/rules/shared/task-toml-supported-fields-only.mdc"

ALLOWED_ROOT_KEYS = frozenset({"version", "metadata", "agent", "verifier", "environment"})
ALLOWED_METADATA = frozenset(
    {
        "author_name",
        "author_email",
        "difficulty",
        "category",
        "subcategories",
        "number_of_milestones",
        "codebase_size",
        "languages",
        "tags",
        "expert_time_estimate_min",
        "junior_time_estimate_min",
    }
)
COMPOSE_ONLY_METADATA = frozenset({"custom_docker_compose", "is_multi_container"})
ALLOWED_AGENT = frozenset({"timeout_sec"})
ALLOWED_VERIFIER = frozenset({"timeout_sec"})
ALLOWED_ENVIRONMENT = frozenset(
    {
        "build_timeout_sec",
        "cpus",
        "memory_mb",
        "storage_mb",
        "workdir",
        "allow_internet",
        "docker_flags",
        "gpus",
        "gpu_types",
    }
)

SECTION_HEADER = re.compile(r"^\[([^\]]+)\]\s*$")
ARRAY_TABLE = re.compile(r"^\[\[([^\]]+)\]\]\s*$")
KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")


def resolve_task_dir(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def has_compose(task_dir: Path) -> bool:
    env = task_dir / "environment"
    return (env / "docker-compose.yaml").is_file() or (env / "docker-compose.yml").is_file()


def check_task_toml(task_dir: Path) -> tuple[bool, list[str]]:
    path = task_dir / "task.toml"
    if not path.is_file():
        return False, [f"missing {path}"]

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    compose = has_compose(task_dir)
    allowed_meta = ALLOWED_METADATA | (COMPOSE_ONLY_METADATA if compose else frozenset())

    section: str | None = None  # None = root before first table
    seen_root_tables: set[str] = set()

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        am = ARRAY_TABLE.match(line.strip())
        if am:
            name = am.group(1).strip()
            errors.append(
                f"line {lineno}: [[{name}]] is not allowed in this project "
                f"(single-step only; no milestone [[steps]]); see {RULE}"
            )
            section = name
            continue

        sm = SECTION_HEADER.match(line.strip())
        if sm:
            name = sm.group(1).strip()
            top = name.split(".", 1)[0]
            if top == "steps" or name.startswith("steps"):
                errors.append(
                    f"line {lineno}: [{name}] milestone layout is blocked; "
                    f"submit a single-step task; see {RULE}"
                )
                section = name
                continue
            if "." in name:
                errors.append(
                    f"line {lineno}: nested table [{name}] is not in the official skeleton; see {RULE}"
                )
                section = name
                continue
            if name not in ALLOWED_ROOT_KEYS - {"version"}:
                errors.append(
                    f"line {lineno}: unsupported table [{name}] — not in official task.toml skeleton; see {RULE}"
                )
            seen_root_tables.add(name)
            section = name
            continue

        km = KEY_LINE.match(line.strip())
        if not km:
            continue
        key = km.group(1)

        if section is None:
            if key not in {"version"}:
                errors.append(
                    f"line {lineno}: unsupported root key '{key}' — only 'version' is allowed; see {RULE}"
                )
            continue

        if section == "metadata":
            if key not in allowed_meta:
                if key in COMPOSE_ONLY_METADATA and not compose:
                    errors.append(
                        f"line {lineno}: metadata.{key} is only allowed when "
                        f"environment/docker-compose.yaml exists; see {RULE}"
                    )
                else:
                    errors.append(
                        f"line {lineno}: unsupported metadata field '{key}' — "
                        f"not in official skeleton; see {RULE}"
                    )
        elif section == "agent":
            if key not in ALLOWED_AGENT:
                errors.append(
                    f"line {lineno}: unsupported agent field '{key}'; see {RULE}"
                )
        elif section == "verifier":
            if key not in ALLOWED_VERIFIER:
                errors.append(
                    f"line {lineno}: unsupported verifier field '{key}'; see {RULE}"
                )
        elif section == "environment":
            if key not in ALLOWED_ENVIRONMENT:
                errors.append(
                    f"line {lineno}: unsupported environment field '{key}'; see {RULE}"
                )
        # unknown section already reported at header

    # Detect bare "steps =" at root via KEY in no section already covered;
    # also flag if file mentions [[steps]] with weird spacing handled above.
    if re.search(r"(?m)^steps\s*=", text):
        errors.append(
            f"unsupported root key 'steps' — milestone layout blocked; see {RULE}"
        )

    return (len(errors) == 0), errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=str, required=True, help="tasks/<name>")
    parser.add_argument("--check", action="store_true", help="Verify; exit 1 on unsupported fields")
    parser.add_argument("--ensure", action="store_true", help="Alias for --check")
    parser.add_argument("--quiet", action="store_true", help="No output on success")
    args = parser.parse_args()

    if not (args.check or args.ensure):
        parser.error("pass --check or --ensure")

    ok, errs = check_task_toml(resolve_task_dir(args.task_dir))
    if ok:
        if not args.quiet:
            print("OK task.toml supported fields only")
        return 0

    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
