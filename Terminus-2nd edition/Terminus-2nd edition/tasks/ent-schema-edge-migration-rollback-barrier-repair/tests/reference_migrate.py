"""Independent reference for entmigrate schema edge migrations."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

APP = Path("/app")
BUNDLED_CATALOG = APP / "fixtures/catalogs/bundled-v3.json"
_DEFAULT_HIDDEN = Path("/opt/verifier-fixtures/ent-edge/hidden-orphan-v3.json")
HIDDEN_CATALOG_NAME = "hidden-orphan-v3.json"

UP_PHASES = [
    "codegen_refresh",
    "atlas_snapshot",
    "ent_pre_validate",
    "add_author_nullable",
    "backfill_author",
    "ent_post_validate",
    "set_author_not_null",
    "add_post_author_fk",
    "add_author_index",
]

DOWN_PHASES = [
    "drop_post_author_fk",
    "drop_author_index",
    "drop_author_not_null",
    "drop_author_column",
]

_UP_PHASE_CONST = {
    "codegen_refresh": "phaseCodegen",
    "atlas_snapshot": "phaseSnapshot",
    "ent_pre_validate": "phasePreValidate",
    "add_author_nullable": "phaseAddColumn",
    "backfill_author": "phaseBackfill",
    "ent_post_validate": "phasePostValidate",
    "set_author_not_null": "phaseNotNull",
    "add_post_author_fk": "phaseAddFK",
    "add_author_index": "phaseAddIndex",
}


def resolve_hidden_catalog() -> Path:
    """Return hidden orphan catalog path (TB3_CATALOG_DIR override or default fixture)."""
    tb3 = os.environ.get("TB3_CATALOG_DIR", "").strip()
    if tb3:
        return Path(tb3) / HIDDEN_CATALOG_NAME
    return _DEFAULT_HIDDEN


def _synthesize_golden_patch(name: str) -> str:
    """Build corrected module source for isolation probes from contract constants."""
    if name == "generator.go":
        lines = ",\n\t\t".join(_UP_PHASE_CONST[p] for p in UP_PHASES)
        return f"""package migrate

// PlanUp returns the ordered up-migration phases for the post_author edge.
func PlanUp() []phase {{
\treturn []phase{{
\t\t{lines},
\t}}
}}
"""
    if name == "applier.go":
        lines = ",\n\t\t".join(f'"{p}"' for p in DOWN_PHASES)
        return f"""package migrate

// PlanDown returns rollback phases for reverting schema version 3.
func PlanDown() []phase {{
\treturn []phase{{
\t\t{lines},
\t}}
}}
"""
    if name == "backfill.go":
        return """package migrate

import (
	"database/sql"
)

// BackfillAuthor copies user_ref into author_id for posts.
func BackfillAuthor(conn *sql.DB) error {
	_, err := conn.Exec(`
UPDATE posts
SET author_id = CAST(substr(user_ref, 3) AS INTEGER)
WHERE author_id IS NULL AND user_ref LIKE 'u:%';
UPDATE posts
SET author_id = CAST(user_ref AS INTEGER)
WHERE author_id IS NULL
  AND user_ref GLOB '[0-9]*'
  AND user_ref NOT GLOB '*[^0-9]*'
`)
	return err
}
"""
    if name == "refresh.go":
        return """package codegen

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"

	"github.com/terminus/ent-migrate/internal/model"
)

// Refresh computes the ent codegen fingerprint for the catalog seed.
func Refresh(cat *model.Catalog) (string, error) {
	sum := sha256.Sum256([]byte(fmt.Sprintf("ent-codegen:%s:v%d", cat.CodegenSeed, cat.TargetVersion)))
	return hex.EncodeToString(sum[:8]), nil
}
"""
    raise FileNotFoundError(name)


def load_golden_patch(name: str) -> str:
    """Load expected module source for single-file isolation probes."""
    oracle_path = Path("/oracle/files") / name
    if oracle_path.is_file():
        return oracle_path.read_text(encoding="utf-8")
    return _synthesize_golden_patch(name)


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_codegen_hash(catalog: dict[str, Any]) -> str:
    seed = catalog["codegen_seed"]
    target = catalog["target_version"]
    digest = hashlib.sha256(f"ent-codegen:{seed}:v{target}".encode()).hexdigest()
    return digest[:16]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def schema_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
    ).fetchone()
    if row is None:
        return 0
    return int(conn.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()[0])


def count_orphans(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS n FROM posts p
        LEFT JOIN users u ON u.id = p.author_id
        WHERE p.author_id IS NOT NULL AND u.id IS NULL
        """
    ).fetchone()
    return int(row["n"])


def count_posts(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0])


def has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def index_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?",
        (name,),
    ).fetchone()
    return int(row[0]) > 0


def trigger_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name=?",
        (name,),
    ).fetchone()
    return int(row[0]) > 0


def backfilled_author_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM posts WHERE author_id IS NOT NULL"
    ).fetchone()
    return int(row[0])


def assert_event_order(events: list[dict[str, Any]]) -> None:
    phases = [e["phase"] for e in events]
    codegen_idx = phases.index("codegen_refresh")
    snapshot_idx = phases.index("atlas_snapshot")
    assert codegen_idx < snapshot_idx, "codegen must precede atlas snapshot"
    assert phases[: len(UP_PHASES)] == UP_PHASES, phases
