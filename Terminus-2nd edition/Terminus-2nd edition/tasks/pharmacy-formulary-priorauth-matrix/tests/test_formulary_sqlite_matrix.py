"""SQLite refresh persistence and publish-matrix gate checks."""

from __future__ import annotations

import sqlite3

from formulatrix_runner import (
    FX_BIN,
    FX_BUNDLE,
    FX_DB,
    FX_MATRIX,
    fx_clean_state,
    fx_invoke,
    fx_read_json,
)


class FormularySqliteMatrix:
    def test_fxs01_repeat_refresh_row_totals(self) -> None:
        """Double refresh-db keeps matrix_rows count stable under UPSERT."""
        fx_clean_state()
        for _ in range(2):
            fx_invoke([FX_BIN, "load-scenario", "--scenario", "sqlite-dual-refresh", "--fixture-dir", str(FX_BUNDLE)])
            proc = fx_invoke([FX_BIN, "refresh-db", "--scenario", "sqlite-dual-refresh"])
            assert proc.returncode == 0, proc.stderr + proc.stdout
        conn = sqlite3.connect(FX_DB)
        try:
            count = conn.execute("SELECT COUNT(*) FROM matrix_rows").fetchone()[0]
        finally:
            conn.close()
        assert count == 2

    def test_fxs02_db_file_after_compile(self) -> None:
        """refresh-db writes /app/state/formulary.db."""
        fx_clean_state()
        fx_invoke([FX_BIN, "load-scenario", "--scenario", "sqlite-dual-refresh", "--fixture-dir", str(FX_BUNDLE)])
        fx_invoke([FX_BIN, "refresh-db", "--scenario", "sqlite-dual-refresh"])
        assert FX_DB.is_file()

    def test_fxs03_matrix_publish_needs_compile(self) -> None:
        """publish-matrix fails when refresh_revision has not been sealed."""
        fx_clean_state()
        fx_invoke([FX_BIN, "load-scenario", "--scenario", "matrix-publish", "--fixture-dir", str(FX_BUNDLE)])
        proc = fx_invoke([FX_BIN, "publish-matrix", "--scenario", "matrix-publish"])
        assert proc.returncode != 0

    def test_fxs04_matrix_json_written(self) -> None:
        """publish-matrix writes formulary-matrix.json under /app/output."""
        fx_clean_state()
        fx_invoke([FX_BIN, "load-scenario", "--scenario", "matrix-publish", "--fixture-dir", str(FX_BUNDLE)])
        fx_invoke([FX_BIN, "refresh-db", "--scenario", "matrix-publish"])
        proc = fx_invoke([FX_BIN, "publish-matrix", "--scenario", "matrix-publish"])
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert FX_MATRIX.is_file()
        body = fx_read_json(FX_MATRIX)
        assert body["row_count"] >= 1

    def test_fxs05_repeat_compile_same_digestcheck(self) -> None:
        """Repeated refresh and publish keep matrix_digest unchanged."""
        fx_clean_state()
        fx_invoke([FX_BIN, "load-scenario", "--scenario", "sqlite-dual-refresh", "--fixture-dir", str(FX_BUNDLE)])
        fx_invoke([FX_BIN, "refresh-db", "--scenario", "sqlite-dual-refresh"])
        fx_invoke([FX_BIN, "publish-matrix", "--scenario", "sqlite-dual-refresh"])
        first = fx_read_json(FX_MATRIX)
        fx_invoke([FX_BIN, "refresh-db", "--scenario", "sqlite-dual-refresh"])
        fx_invoke([FX_BIN, "publish-matrix", "--scenario", "sqlite-dual-refresh"])
        second = fx_read_json(FX_MATRIX)
        assert first["matrix_digest"] == second["matrix_digest"]
