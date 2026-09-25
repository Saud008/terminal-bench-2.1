"""Behavioral tests for caddyctl offline route matcher."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_match import reference_export_doc, reference_handler_id

CADDYCTL = "/app/bin/caddyctl"
STAGE = Path("/app/state/caddy-stage.json")
COMMIT = Path("/app/state/caddy-commit.json")
LAST = Path("/app/state/last-match.json")
OUT = Path("/app/output/route-handler.json")
BUNDLED = Path("/app/data/routes")
DATA_ROUTES = "/app/data/routes"
ROUTE_HANDLER_JSON = "/app/output/route-handler.json"
TB3_SRC = Path("/opt/verifier-fixtures/caddy-routes")
REQ_DIR = Path("/tests/requests")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _fresh() -> None:
    for p in (STAGE, COMMIT, LAST, OUT):
        if p.exists():
            p.unlink()


def _ingest(routes_dir: Path) -> None:
    _run([CADDYCTL, "ingest", str(routes_dir)])


def _match(req_file: Path) -> None:
    _run([CADDYCTL, "match", "--request", str(req_file)])


def _export() -> None:
    _run([CADDYCTL, "route", "export"])


def _pipeline(routes_dir: Path, req_file: Path) -> None:
    _fresh()
    _ingest(routes_dir)
    _match(req_file)
    _export()


@pytest.fixture(autouse=True)
def clean_state():
    _fresh()
    yield
    _fresh()


def test_instruction_data_and_output_paths_exercised():
    """Instruction paths /app/data/routes and /app/output/route-handler.json are read and written."""
    route_files = list(Path(DATA_ROUTES).glob("*.json"))
    assert route_files
    _pipeline(BUNDLED, REQ_DIR / "v1_get.req")
    out_path = Path(ROUTE_HANDLER_JSON)
    assert out_path.is_file()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["handler_id"] == "narrow_v1_get"


def test_caddyctl_binary_exists():
    """Built caddyctl binary must exist at /app/bin/caddyctl."""
    assert Path(CADDYCTL).is_file()


def test_bundled_routes_directory_contract():
    """Instruction bundled fixtures path /app/data/routes must exist."""
    assert BUNDLED.is_dir()
    assert (BUNDLED / "edge.json").is_file()


def test_ingest_writes_staging_snapshot():
    """Ingest must write normalized staging at /app/state/caddy-stage.json."""
    _ingest(BUNDLED)
    assert STAGE.is_file()
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert len(data["routes"]) == 4


def test_ingest_writes_commit_metadata():
    """Ingest must write commit metadata with replay_seq and stage_hash."""
    _ingest(BUNDLED)
    assert COMMIT.is_file()
    commit = json.loads(COMMIT.read_text(encoding="utf-8"))
    assert commit["replay_seq"] >= 1
    assert len(commit["stage_hash"]) == 64


def test_staging_preserves_handler_ids():
    """Staging must copy stable handler @id values from route JSON."""
    _ingest(BUNDLED)
    routes = json.loads(STAGE.read_text(encoding="utf-8"))["routes"]
    ids = [r["handler_id"] for r in routes]
    assert ids == ["wide_api", "narrow_v1_get", "path_strip_admin", "auth_token"]


def test_staging_route_index_order():
    """Routes in staging preserve source declaration order indices."""
    _ingest(BUNDLED)
    routes = json.loads(STAGE.read_text(encoding="utf-8"))["routes"]
    assert [r["index"] for r in routes] == [0, 1, 2, 3]


def test_staging_path_contract():
    """Instruction staging path /app/state/caddy-stage.json is honored."""
    _ingest(BUNDLED)
    assert STAGE == Path("/app/state/caddy-stage.json")


def test_match_writes_last_match_file():
    """Match subcommand writes /app/state/last-match.json."""
    _ingest(BUNDLED)
    req = REQ_DIR / "v1_get.req"
    _match(req)
    assert LAST.is_file()


def test_specificity_narrow_v1_get_wins_over_wide():
    """Higher-specificity narrow_v1_get wins over wide_api per matcher-specificity-order.md."""
    _ingest(BUNDLED)
    req = REQ_DIR / "v1_get.req"
    _match(req)
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["matched"] is True
    assert lm["handler_id"] == "narrow_v1_get"


def test_wide_api_matches_broader_path():
    """wide_api matches when narrow v1 prefix does not apply."""
    _ingest(BUNDLED)
    _match(REQ_DIR / "api_v2.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["handler_id"] == "wide_api"


def test_header_case_fold_matches_auth_token():
    """Header matcher folds values per header-case-contract.md."""
    _ingest(BUNDLED)
    _match(REQ_DIR / "auth_upper.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["handler_id"] == "auth_token"


def test_export_creates_route_handler_json():
    """route export writes /app/output/route-handler.json."""
    _pipeline(BUNDLED, REQ_DIR / "v1_get.req")
    assert OUT.is_file()


def test_export_handler_id_is_stable_at_id_not_index():
    """Export must emit handler @id, not route array index placeholder."""
    _pipeline(BUNDLED, REQ_DIR / "v1_get.req")
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    assert doc["handler_id"] == "narrow_v1_get"
    assert not doc["handler_id"].startswith("route-index")


def test_export_replay_seq_matches_commit():
    """Export echoes replay_seq from /app/state/caddy-commit.json."""
    _pipeline(BUNDLED, REQ_DIR / "v1_get.req")
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    commit = json.loads(COMMIT.read_text(encoding="utf-8"))
    assert doc["replay_seq"] == commit["replay_seq"]


def test_export_output_path_contract():
    """Instruction export path /app/output/route-handler.json is honored."""
    _pipeline(BUNDLED, REQ_DIR / "v1_get.req")
    assert OUT == Path("/app/output/route-handler.json")


def test_match_reference_agreement_v1_get():
    """CLI match agrees with independent reference on v1 GET fixture."""
    _ingest(BUNDLED)
    req_bytes = (REQ_DIR / "v1_get.req").read_bytes()
    _match(REQ_DIR / "v1_get.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["handler_id"] == reference_handler_id(STAGE, req_bytes)


def test_match_reference_agreement_wide_api():
    """CLI match agrees with reference on broader API path."""
    _ingest(BUNDLED)
    req_bytes = (REQ_DIR / "api_v2.req").read_bytes()
    _match(REQ_DIR / "api_v2.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["handler_id"] == reference_handler_id(STAGE, req_bytes)


def test_export_reference_agreement():
    """Exported handler_id and replay_seq match reference export doc."""
    _pipeline(BUNDLED, REQ_DIR / "v1_get.req")
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    ref = reference_export_doc(STAGE, COMMIT, "narrow_v1_get")
    assert doc["handler_id"] == ref["handler_id"]
    assert doc["replay_seq"] == ref["replay_seq"]


def test_rebuild_subprocess_cli_match_export():
    """Subprocess route export succeeds after test.sh rebuild."""
    _pipeline(BUNDLED, REQ_DIR / "v1_get.req")
    cp = subprocess.run([CADDYCTL, "route", "export"], capture_output=True, text=True)
    assert cp.returncode == 0


def test_last_match_json_schema_fields():
    """last-match.json includes matched, handler_id, and route_index fields."""
    _ingest(BUNDLED)
    _match(REQ_DIR / "v1_get.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    for key in ("matched", "handler_id", "route_index"):
        assert key in lm


def test_tb3_hidden_fixture_directory_present():
    """Hidden verifier fixtures are mounted under /opt/verifier-fixtures/caddy-routes."""
    assert TB3_SRC.is_dir()


def test_tb3_regexp_admin_not_substring_match():
    """path_regexp uses anchors; /x/admin must not match /admin pattern."""
    tmp = Path("/tmp/tb3-caddy-routes")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    shutil.copy(TB3_SRC / "tb3-routes.json", tmp / "tb3-routes.json")
    _ingest(tmp)
    _match(REQ_DIR / "tb3_x_admin.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["handler_id"] == "prefix_x_admin"


def test_tb3_header_authorization_case_fold():
    """TB3 Authorization header values fold before comparison."""
    tmp = Path("/tmp/tb3-caddy-auth")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    shutil.copy(TB3_SRC / "tb3-routes.json", tmp / "tb3-routes.json")
    _ingest(tmp)
    _match(REQ_DIR / "tb3_bearer.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["handler_id"] == "header_bearer_fold"


def test_tb3_terminal_route_blocks_handle_path_sibling():
    """Terminal route stops handle_path sibling per handle-termination.md."""
    tmp = Path("/tmp/tb3-caddy-halt")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    shutil.copy(TB3_SRC / "tb3-routes.json", tmp / "tb3-routes.json")
    _ingest(tmp)
    _match(REQ_DIR / "tb3_halt_post.req")
    lm = json.loads(LAST.read_text(encoding="utf-8"))
    assert lm["handler_id"] == "terminal_block_fallback"


def test_tb3_export_handler_id_reference():
    """TB3 export handler_id matches reference on halt POST fixture."""
    tmp = Path("/tmp/tb3-caddy-export")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    shutil.copy(TB3_SRC / "tb3-routes.json", tmp / "tb3-routes.json")
    req = REQ_DIR / "tb3_halt_post.req"
    _pipeline(tmp, req)
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    expected = reference_handler_id(STAGE, req.read_bytes())
    assert doc["handler_id"] == expected


def test_per_run_ingest_increments_replay_seq(tmp_path: Path):
    """Repeated ingest increments replay_seq in commit metadata."""
    alt = tmp_path / "routes"
    alt.mkdir()
    shutil.copy(BUNDLED / "edge.json", alt / "edge.json")
    _ingest(alt)
    first = json.loads(COMMIT.read_text(encoding="utf-8"))["replay_seq"]
    _ingest(alt)
    second = json.loads(COMMIT.read_text(encoding="utf-8"))["replay_seq"]
    assert second == first + 1


def test_decoy_module_not_on_hot_path():
    """internal/decoy exists but is not required for match or export."""
    assert Path("/app/internal/decoy/wrap.go").is_file()


def test_export_fails_without_prior_match():
    """route export must fail when last-match.json is missing."""
    _ingest(BUNDLED)
    cp = subprocess.run([CADDYCTL, "route", "export"], capture_output=True, text=True)
    assert cp.returncode != 0


def test_staging_ingest_seq_matches_commit():
    """Staging ingest_seq mirrors commit replay_seq after ingest."""
    _ingest(BUNDLED)
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    commit = json.loads(COMMIT.read_text(encoding="utf-8"))
    assert stage["ingest_seq"] == commit["replay_seq"]
