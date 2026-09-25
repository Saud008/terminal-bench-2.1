from __future__ import annotations

import os
import sys

from musdoss import catalog, compose, config, publish, vault


def _usage() -> None:
    print("usage: musdoss vault load|compose align|publish dossier ...", file=sys.stderr)


def _archive_dir(cfg: dict) -> str:
    return os.environ.get("TB3_ARCHIVE_DIR") or cfg["archive_dir"]


def main() -> None:
    if len(sys.argv) < 2:
        _usage()
        raise SystemExit(2)
    cfg = config.load_config("/app/config/musdoss.json")
    cmd = sys.argv[1]
    try:
        if cmd == "vault" and len(sys.argv) >= 3 and sys.argv[2] == "load":
            _run_vault_load(cfg)
        elif cmd == "compose" and len(sys.argv) >= 3 and sys.argv[2] == "align":
            _run_compose_align(cfg)
        elif cmd == "publish" and len(sys.argv) >= 3 and sys.argv[2] == "dossier":
            _run_publish(cfg)
        else:
            _usage()
            raise SystemExit(2)
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc


def _parse_flags(argv: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    idx = 0
    while idx < len(argv):
        if argv[idx].startswith("--"):
            key = argv[idx][2:]
            if idx + 1 >= len(argv):
                raise ValueError(f"missing value for --{key}")
            out[key] = argv[idx + 1]
            idx += 2
        else:
            idx += 1
    return out


def _run_vault_load(cfg: dict) -> None:
    flags = _parse_flags(sys.argv[3:])
    seed = flags.get("seed", "")
    archive = flags.get("archive", "")
    if not seed or not archive:
        raise ValueError("seed and archive required")
    path = catalog.archive_path(_archive_dir(cfg), archive)
    arch = catalog.load_archive(path, seed)
    vault.write_vault_snapshot(cfg["vault_snapshot_path"], seed, archive, arch)


def _run_compose_align(cfg: dict) -> None:
    flags = _parse_flags(sys.argv[3:])
    seed = flags.get("seed", "")
    archive = flags.get("archive", "")
    if not seed or not archive:
        raise ValueError("seed and archive required")
    compose.run_align(seed, archive, cfg["vault_snapshot_path"], cfg["accession_db_path"])


def _run_publish(cfg: dict) -> None:
    flags = _parse_flags(sys.argv[3:])
    seed = flags.get("seed", "")
    archive = flags.get("archive", "")
    output = flags.get("output", "")
    if not seed or not archive or not output:
        raise ValueError("seed, archive, output required")
    rep = publish.build_dossier(cfg["vault_snapshot_path"], cfg["accession_db_path"], seed, archive)
    from musdoss import emit

    emit.write_dossier(output, rep)


if __name__ == "__main__":
    main()
