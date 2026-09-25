"""Behavioral verifier for paramgate parameter policy attestation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest
from paramgate_policy_ref import bind_get, expected_snapshot

APP = Path("/app")
BASE = "http://127.0.0.1:8080"
RESET = APP / "scripts/reset-state.sh"
START = APP / "scripts/start-server.sh"
SNAPSHOT = APP / "state/bind-snapshot.json"
HIDDEN_FIXTURES = Path(os.environ.get("TB3_FIXTURE_DIR", "/opt/verifier-fixtures"))

PROTECTED_SHA256: dict[str, str] = {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _populate_hashes() -> None:
    for rel in (
        "fixtures/openapi-base.yaml",
        "fixtures/admin-paths.yaml",
        "config/paramgate.yaml",
    ):
        PROTECTED_SHA256[rel] = _sha256(APP / rel)


_populate_hashes()


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def reset_and_start() -> None:
    assert _run(["bash", str(RESET)]).returncode == 0
    assert _run(["bash", str(START)]).returncode == 0


def http_get(path: str, query: str = "") -> tuple[int, dict]:
    url = f"{BASE}{path}"
    if query:
        url = f"{url}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        return exc.code, body


def http_post(path: str, body: bytes, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        method="POST",
        headers=headers or {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


@pytest.fixture(autouse=True)
def _fresh_server() -> None:
    reset_and_start()


def test_protected_contract_fixtures_unchanged() -> None:
    """OpenAPI trust contract fixtures must remain tamper-free."""
    for rel, expect in PROTECTED_SHA256.items():
        assert _sha256(APP / rel) == expect, rel


def test_form_explode_false_array_uses_comma_delimiter() -> None:
    """Ingest stage must split query arrays with form style and explode false on commas."""
    q = "tenant=acme&tags=alpha,beta,gamma"
    status, body = http_get("/v1/catalog/items", q)
    assert status == 200
    assert body["params"]["tags"] == ["alpha", "beta", "gamma"]


def test_form_explode_true_array_uses_repeated_keys() -> None:
    """Query arrays with form style and explode true must preserve repeated keys."""
    q = "include=stock&include=price"
    status, body = http_get("/v1/catalog/items/SKU-9", q)
    assert status == 200
    assert body["params"]["include"] == ["stock", "price"]


def test_deep_object_bracket_notation() -> None:
    """deepObject parameters must bind bracket-encoded object fields."""
    q = "tenant=acme&filter[status]=open&filter[priority]=high"
    status, body = http_get("/v1/catalog/items", q)
    assert status == 200
    assert body["params"]["filter"] == {"priority": "high", "status": "open"}


def test_form_object_explode_false_comma_pairs() -> None:
    """Form-style objects with explode false must bind comma-separated key=value pairs."""
    q = "tenant=acme&meta=region=us,shard=3"
    status, body = http_get("/v1/catalog/items", q)
    assert status == 200
    assert body["params"]["meta"] == {"region": "us", "shard": "3"}


def test_date_normalizes_to_utc_calendar_day() -> None:
    """Date query parameters must normalize to UTC calendar day without local drift."""
    q = "tenant=acme&since=2024-06-15T23:30:00-07:00"
    status, body = http_get("/v1/catalog/items", q)
    assert status == 200
    assert body["params"]["since"] == "2024-06-16"


def test_missing_required_query_returns_policy_violation() -> None:
    """Missing required parameters must return HTTP 400 invalid missing_required."""
    status, body = http_get("/v1/catalog/items")
    assert status == 400
    assert body["status"] == "invalid"
    assert body["reason"] == "missing_required"


def test_admin_extension_route_requires_actor() -> None:
    """Merged admin OpenAPI fragment routes must enforce required actor policy."""
    status, body = http_get("/v1/admin/audit")
    assert status == 400
    assert body["reason"] == "missing_required"


def test_admin_window_object_key_order_canonical() -> None:
    """Admin deepObject window fields must canonicalize nested keys lexicographically."""
    q = "actor=ops&window[end]=2024-01-31&window[start]=2024-01-01"
    status, body = http_get("/v1/admin/audit", q)
    assert status == 200
    assert body["params"]["window"] == {"end": "2024-01-31", "start": "2024-01-01"}


def test_witness_snapshot_written_on_success() -> None:
    """Successful policy evaluation must seal params into bind-snapshot.json witness."""
    q = "tenant=acme&tags=a,b"
    status, _ = http_get("/v1/catalog/items", q)
    assert status == 200
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["route"] == "/v1/catalog/items"
    assert snap["params"]["tenant"] == "acme"


def test_response_params_match_witness_snapshot() -> None:
    """Export stage must emit HTTP params from staged witness, not empty maps."""
    q = "tenant=acme&tags=x,y"
    status, body = http_get("/v1/catalog/items", q)
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert status == 200
    assert body["params"] == snap["params"]


def test_bind_seq_increments_across_requests() -> None:
    """Witness bind_seq must increment monotonically across successful attestation."""
    http_get("/v1/catalog/items", "tenant=acme")
    first = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["bind_seq"]
    http_get("/v1/catalog/items", "tenant=acme")
    second = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["bind_seq"]
    assert second == first + 1


def test_post_notes_requires_request_id_header() -> None:
    """POST catalog notes must enforce required X-Request-Id header policy."""
    status, body = http_post("/v1/catalog/notes", b'{"text":"hi"}')
    assert status == 400
    assert body["reason"] == "missing_required"


def test_post_notes_json_body_in_response() -> None:
    """POST notes success must include decoded JSON body in witness-backed response."""
    status, body = http_post(
        "/v1/catalog/notes",
        b'{"text":"policy-checked"}',
        {"Content-Type": "application/json", "X-Request-Id": "req-1"},
    )
    assert status == 200
    assert body["body"]["text"] == "policy-checked"


def test_latin1_json_body_transcoded() -> None:
    """Latin-1 JSON bodies must transcode to UTF-8 before policy evaluation."""
    raw = b'{"text":"caf\xe9"}'
    status, body = http_post(
        "/v1/catalog/notes",
        raw,
        {
            "Content-Type": "application/json; charset=iso-8859-1",
            "X-Request-Id": "req-latin1",
        },
    )
    assert status == 200
    assert body["body"]["text"] == "café"


def test_reference_parity_catalog_items() -> None:
    """Catalog item binding must match independent reference policy math."""
    q = "tenant=ref&filter[status]=open&filter[priority]=low&tags=a,b"
    expect = bind_get("/v1/catalog/items", q)
    status, body = http_get("/v1/catalog/items", q)
    assert status == 200
    assert body["params"] == expect


def test_reference_parity_admin_audit() -> None:
    """Admin audit binding must match independent reference policy math."""
    q = "actor=bot&scopes=read&scopes=write"
    status, body = http_get("/v1/admin/audit", q)
    assert status == 200
    assert body["params"]["scopes"] == ["read", "write"]


def test_tb3_hidden_filter_key_order() -> None:
    """Hidden TB3 fixture must enforce canonical nested filter key order."""
    case = json.loads((HIDDEN_FIXTURES / "tb3-binding-cases.json").read_text(encoding="utf-8"))["cases"][0]
    status, body = http_get(case["path"], case["query"])
    expect = expected_snapshot(case["method"], case["path"], case["query"])
    assert status == 200
    assert body["params"] == expect["params"]


def test_tb3_hidden_admin_window_order() -> None:
    """Hidden TB3 admin window fixture must canonicalize nested object field order."""
    case = json.loads((HIDDEN_FIXTURES / "tb3-binding-cases.json").read_text(encoding="utf-8"))["cases"][1]
    status, body = http_get(case["path"], case["query"])
    expect = expected_snapshot(case["method"], case["path"], case["query"])
    assert status == 200
    assert body["params"] == expect["params"]


def test_tb3_hidden_form_meta_object() -> None:
    """Hidden TB3 form meta fixture must bind comma-separated object pairs."""
    case = json.loads((HIDDEN_FIXTURES / "tb3-binding-cases.json").read_text(encoding="utf-8"))["cases"][2]
    status, body = http_get(case["path"], case["query"])
    expect = expected_snapshot(case["method"], case["path"], case["query"])
    assert status == 200
    assert body["params"] == expect["params"]


def test_invalid_path_returns_not_found() -> None:
    """Unknown routes must return HTTP 404 not_found without staging witness artifacts."""
    status, body = http_get("/v1/unknown/route")
    assert status == 404
    assert body["status"] == "not_found"


def test_bad_content_type_rejected() -> None:
    """Non-JSON content types on JSON routes must fail policy with bad_content_type."""
    status, body = http_post(
        "/v1/catalog/notes",
        b"plain",
        {"Content-Type": "text/plain", "X-Request-Id": "req-bad"},
    )
    assert status == 400
    assert body["reason"] == "bad_content_type"
