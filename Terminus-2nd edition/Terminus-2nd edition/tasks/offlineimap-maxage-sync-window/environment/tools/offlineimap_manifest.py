from dataclasses import dataclass
from pathlib import Path


@dataclass
class ManifestRow:
    folder: str
    internal_date: int
    size_bytes: int
    uid: int


def load_manifest(path: Path) -> list[ManifestRow]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("folder\t")
    rows: list[ManifestRow] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        folder, idate, size, uid = line.split("\t")
        rows.append(
            ManifestRow(
                folder=folder,
                internal_date=int(idate),
                size_bytes=int(size),
                uid=int(uid),
            )
        )
    return rows
