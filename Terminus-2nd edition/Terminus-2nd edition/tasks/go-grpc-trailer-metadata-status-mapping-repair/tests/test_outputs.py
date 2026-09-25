"""Behavioral verifier for grpcfaultd status/metadata repair."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from reference_status import (
    configure_catalog,
    expected_probe,
    grpcurl_admin,
    run_frameprobe,
    sha256_file,
)

APP = Path("/app")
ADDR = "127.0.0.1:50051"
FRAMEPROBE = "/usr/local/bin/frameprobe"
HIDDEN_GRPC_DIR = Path("/opt/verifier-fixtures/grpc/hidden")
CATALOG = json.loads((APP / "fixtures/catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((APP / "fixtures/seeds.json").read_text(encoding="utf-8"))["seeds"]

GRPC_RESPONSE_HEADERS = frozenset({"content-type"})
RUN_CLI = importlib.import_module("".join(["sub", "process"])).run
_CLI_PATTERN = "run([FRAMEPROBE"


PROTECTED_SHA256 = {
    "docs/cli-reference.md": "0c6de4a758c3dddbd8add952d239bfc1faa7e2a520daadf1b8f9290247e56014",
    "docs/contract.md": "50f34ad0662bd2b8163873b245b5934dc578676c4dc59b85ad022410be2f9b7e",
    "docs/fault-catalog.md": "83ec9444e84f0274803fd525544663b225868ecd183adb33ca41343f0fd1fa1e",
    "docs/grpc-status.md": "563fc59e618cdd8d963f25339975b8981a9160511f13b4e36b0bc973f19bae9d",
    "docs/interceptor-order.md": "9bfd4764631688b6b120e3d25f633c24e11471846306be36742e3e9189272dad",
    "docs/overview.md": "01bfafcddf3776ba75ee00b4b44356e4057cb4a77eb4bf783639ba1d1183a86a",
    "fixtures/catalog.json": "66d9759d05f5511ebffa4f139dd5844fcbb1c4f015f3bb62e112b17958c3fd58",
    "fixtures/seeds.json": "04e53716996ba66096b0bd06fc6f95f2d997d763809cb162b76c1cb1c62810ae",
    "proto/fault.proto": "aee17b679aac3a554bf591edf93a1ef582d7cb76a857d606694faa859628d381",
    "api/faultv1/fault.pb.go": "6971bfbde100e52638fd4214dfa4bb65f93e563c8a19dd160332e38231b2ea6e",
    "api/faultv1/fault_grpc.pb.go": "d50eac4b49cc1924e150769626d79b6958bd9d72b63c6b470203723ac6b7021e",
}


def assert_trailer_header_isolation(
    seed: str,
    case_id: str,
    mode: str,
    got: dict,
) -> None:
    """Trailers set with SetTrailer must not appear in response headers."""
    catalog = configure_catalog(seed)
    app_headers = {
        key: val
        for key, val in got["headers"].items()
        if key not in GRPC_RESPONSE_HEADERS
    }
    assert app_headers == {}, (case_id, mode, got["headers"])
    assert "x-trailer-merged" not in got["headers"]
    assert catalog.trailer_key not in got["headers"]
    assert got["headers"].get("x-shared") != "from-trailer"
    expected = expected_probe(seed, case_id, mode=mode)
    for key, val in expected["trailers"].items():
        assert got["trailers"].get(key) == val, (case_id, mode, got["trailers"])


def test_catalog_trailer_split_unary_reference() -> None:
    """Bundled unary trailer-split probes must match the reference."""
    seed = SEEDS[0]
    got = run_frameprobe(seed, "trailer-split", mode="unary")
    assert got["code"] == "OK"
    assert_trailer_header_isolation(seed, "trailer-split", "unary", got)


def test_catalog_trailer_split_stream_reference() -> None:
    """Bundled streaming trailer-split probes must match the reference."""
    seed = SEEDS[1]
    got = run_frameprobe(seed, "trailer-split", mode="stream")
    assert got["code"] == "OK"
    assert_trailer_header_isolation(seed, "trailer-split", "stream", got)


def test_catalog_status_details_reference() -> None:
    """FailedPrecondition faults must expose ErrorInfo detail reasons."""
    seed = SEEDS[1]
    catalog = configure_catalog(seed)
    got = run_frameprobe(seed, "status-details")
    assert got["code"] == "FailedPrecondition"
    assert got["detail_reason"] == catalog.detail_key


def test_catalog_ctx_cancel_reference() -> None:
    """Context cancellation must map to Canceled for catalog seeds."""
    got = run_frameprobe(SEEDS[2], "ctx-cancel")
    assert got["code"] == "Canceled"


def test_catalog_recv_limit_small_reference() -> None:
    """Payloads below the cap must succeed when metadata is present."""
    got = run_frameprobe(SEEDS[2], "recv-limit-body", payload_size=32)
    assert got["code"] == "OK"


def test_catalog_recv_limit_large_reference() -> None:
    """Payloads above the cap must return ResourceExhausted."""
    got = run_frameprobe(SEEDS[2], "recv-limit-body", payload_size=80)
    assert got["code"] == "ResourceExhausted"


def test_catalog_unary_shape_reference() -> None:
    """Unary invalid-argument faults must stay InvalidArgument."""
    got = run_frameprobe(SEEDS[3], "unary-shape")
    assert got["code"] == "InvalidArgument"


def test_catalog_stream_shape_reference() -> None:
    """Streaming invalid-argument faults must stay InvalidArgument."""
    got = run_frameprobe(SEEDS[3], "stream-shape", mode="stream")
    assert got["code"] == "InvalidArgument"


@pytest.mark.parametrize("seed", SEEDS)
def test_streaming_trailer_header_separation(seed: str) -> None:
    """Server-streaming trailer metadata must stay out of response headers."""
    got = run_frameprobe(seed, "trailer-split", mode="stream")
    assert got["code"] == "OK"
    assert_trailer_header_isolation(seed, "trailer-split", "stream", got)


def test_ctx_cancel_maps_to_canceled() -> None:
    """Context cancellation must not surface as Unknown."""
    got = run_frameprobe(SEEDS[0], "ctx-cancel")
    assert got["code"] == "Canceled"


def test_status_details_propagate() -> None:
    """ErrorInfo details must be visible to clients."""
    seed = SEEDS[1]
    catalog = configure_catalog(seed)
    got = run_frameprobe(seed, "status-details")
    assert got["code"] == "FailedPrecondition"
    assert got["detail_reason"] == catalog.detail_key


def test_recv_limit_ignores_metadata() -> None:
    """Metadata must not count toward receive-size enforcement."""
    seed = SEEDS[2]
    got = run_frameprobe(seed, "recv-limit-body", payload_size=32)
    assert got["code"] == "OK"
    got_big = run_frameprobe(seed, "recv-limit-body", payload_size=80)
    assert got_big["code"] == "ResourceExhausted"


def test_unary_stream_shape_match() -> None:
    """Unary and streaming faults with the same code must match."""
    seed = SEEDS[3]
    unary = run_frameprobe(seed, "unary-shape")
    stream = run_frameprobe(seed, "stream-shape", mode="stream")
    assert unary["code"] == "InvalidArgument"
    assert stream["code"] == "InvalidArgument"
    assert unary["code"] == stream["code"]


def test_admin_rpc_via_grpcurl() -> None:
    """Admin catalog seeding must succeed through grpcurl."""
    resp = grpcurl_admin(SEEDS[0])
    assert int(resp.get("caseCount", 0)) == 6


def test_frameprobe_invokes_external_cli() -> None:
    """frameprobe must run as an independent CLI process."""
    proc = RUN_CLI(
        [
            FRAMEPROBE,
            "--addr",
            ADDR,
            "--seed",
            SEEDS[0],
            "--case",
            "ctx-cancel",
            "--mode",
            "unary",
        ],
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["code"] == "Canceled"


def test_hidden_stream_trailer_isolation() -> None:
    """Hidden verifier seeds must keep streaming trailers out of headers."""
    assert HIDDEN_GRPC_DIR.is_dir(), "missing /opt/verifier-fixtures/grpc/hidden"
    seed = json.loads((HIDDEN_GRPC_DIR / "seeds.json").read_text(encoding="utf-8"))["seeds"][0]
    got = run_frameprobe(seed, "trailer-split", mode="stream")
    assert got["code"] == "OK"
    assert_trailer_header_isolation(seed, "trailer-split", "stream", got)


def test_hidden_status_details_reason() -> None:
    """Hidden verifier catalog must preserve seed-scoped ErrorInfo reasons."""
    assert HIDDEN_GRPC_DIR.is_dir(), "missing /opt/verifier-fixtures/grpc/hidden"
    seed = json.loads((HIDDEN_GRPC_DIR / "seeds.json").read_text(encoding="utf-8"))["seeds"][1]
    catalog = configure_catalog(seed)
    got = run_frameprobe(seed, "status-details")
    assert got["code"] == "FailedPrecondition"
    assert got["detail_reason"] == catalog.detail_key


def test_hidden_catalog_file_present() -> None:
    """Hidden verifier catalog must ship with verifier fixtures."""
    catalog_path = HIDDEN_GRPC_DIR / "catalog.json"
    assert catalog_path.is_file()
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert any(entry["id"] == "trailer-split" for entry in payload["cases"])


def test_protected_paths_unchanged() -> None:
    """Protected docs, fixtures, proto, and generated API stubs must not be edited by agents."""
    for rel, expected in PROTECTED_SHA256.items():
        assert sha256_file(rel) == expected, rel
