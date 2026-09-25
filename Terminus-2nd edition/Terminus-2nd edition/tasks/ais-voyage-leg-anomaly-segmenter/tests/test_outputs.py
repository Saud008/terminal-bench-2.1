"""Pytest contract for /app/state/track-snapshot.json and /app/output/voyage-atlas.json

Every behavioral test invokes the aissegment CLI through subprocess helpers.
Coverage spans the feed ingest path and atlas export path end to end.
"""

import shutil
import tempfile

from vts_leg_independent import (
    ATLAS,
    BIN,
    HIDDEN,
    HIDDEN_SHA,
    OUTPUT,
    PORTS,
    PORTS_SHA,
    PROT_SHA,
    SNAPSHOT_PATH,
    STATE,
    STREAMS,
    Path,
    _feed_atlas,
    _leg_ordinal,
    _reset_state,
    _run_cli,
    hashlib,
    json,
    reference_pipeline,
)


def test_t1469c8_ais_vts_leg_contract_output_paths_on_disk() -> None:
    """Deliverables under /app/state and /app/output per instruction."""
    assert str(SNAPSHOT_PATH) == "/app/state/track-snapshot.json"
    assert str(ATLAS) == "/app/output/voyage-atlas.json"
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    assert SNAPSHOT_PATH.is_file()
    assert ATLAS.is_file()
    assert SNAPSHOT_PATH.name == "track-snapshot.json"
    assert ATLAS.name == "voyage-atlas.json"


def test_t1469c8_ais_vts_leg_burst_case_matches_expect() -> None:
    """Independent recomputation matches CLI atlas for burst case."""
    stream = STREAMS / "005-burst-dedupe.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert got == ref


def test_t1469c8_ais_vts_leg_ports_visited_deduped_in_leg() -> None:
    """Leg ports list records first appearance order without consecutive duplicates."""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    for leg in got["voyage_legs"]:
        ports = leg["ports"]
        for i in range(1, len(ports)):
            assert ports[i] != ports[i - 1]


def test_t1469c8_ais_vts_leg_none_port_label_on_open_water() -> None:
    """Open-water points and legs use the documented none port label."""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    first = got["voyage_legs"][0]
    assert first["start_port"] == "none"
    assert "none" in first["ports"]
    assert first == ref["voyage_legs"][0]
    assert any(leg["start_port"] == "none" for leg in got["voyage_legs"])


def test_t1469c8_ais_vts_leg_none_port_draught_only_legs() -> None:
    """Draught-boundary stream stays outside polygons so start/end ports are none."""
    stream = STREAMS / "004-draught-boundary.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert got["voyage_legs"] == ref["voyage_legs"]
    for leg in got["voyage_legs"]:
        assert leg["start_port"] == "none"
        assert leg["end_port"] == "none"
        assert leg["ports"] == ["none"]


def test_t1469c8_ais_vts_leg_atlas_bad_snapshot_rc2() -> None:
    """Malformed snapshot on atlas exits 2."""
    _reset_state()
    STATE.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text("{not-json")
    rc = _run_cli(
        [
            "atlas",
            "--output",
            str(ATLAS),
            "--snapshot",
            str(SNAPSHOT_PATH),
            "--ports",
            str(PORTS),
        ]
    )
    assert rc.returncode == 2


def test_t1469c8_ais_vts_leg_intake_unknown_path_rc1() -> None:
    """Missing feed input exits 1 per cli.md."""
    _reset_state()
    rc = _run_cli(
        [
            "feed",
            "--input",
            "/app/fixtures/streams/does-not-exist.jsonl",
            "--snapshot",
            str(SNAPSHOT_PATH),
            "--ports",
            str(PORTS),
        ]
    )
    assert rc.returncode == 1


def test_t1469c8_ais_vts_leg_overlay_out_of_order_stat() -> None:
    """TB3_AIS_DIR feed records out_of_order in snapshot feed_stats for jitter streams."""
    hidden_name = "006-edge-port-jitter.jsonl"
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        probe = Path(tmp) / hidden_name
        shutil.copy(HIDDEN / hidden_name, probe)
        env = {"TB3_AIS_DIR": tmp}
        _reset_state()
        STATE.mkdir(parents=True, exist_ok=True)
        rc = _run_cli(
            [
                "feed",
                "--input",
                hidden_name,
                "--snapshot",
                str(SNAPSHOT_PATH),
                "--ports",
                str(PORTS),
            ],
            env=env,
        )
        assert rc.returncode == 0, rc.stderr
    snap_doc = json.loads(SNAPSHOT_PATH.read_text())
    ref_snap, _ = reference_pipeline(HIDDEN / hidden_name, PORTS)
    assert (
        snap_doc["feed_stats"]["out_of_order"] == ref_snap["feed_stats"]["out_of_order"]
    )
    assert snap_doc["feed_stats"]["out_of_order"] >= 1


def test_t1469c8_ais_vts_leg_hidden_out_of_order_counter() -> None:
    """Hidden jitter stream reports out_of_order when file seq differs from stable order."""
    hidden = HIDDEN / "006-edge-port-jitter.jsonl"
    _, ref = reference_pipeline(hidden, PORTS)
    assert ref["anomalies"]["out_of_order"] >= 1


def test_t1469c8_ais_vts_leg_overlay_edge_port_jitter() -> None:
    """TB3_AIS_DIR resolves hidden stream basenames with edge port geometry."""
    hidden_name = "006-edge-port-jitter.jsonl"
    assert (HIDDEN / hidden_name).is_file()
    digest = hashlib.sha256((HIDDEN / hidden_name).read_bytes()).hexdigest()
    assert digest == HIDDEN_SHA[hidden_name]
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        probe = Path(tmp) / hidden_name
        shutil.copy(HIDDEN / hidden_name, probe)
        env = {"TB3_AIS_DIR": tmp}
        _reset_state()
        STATE.mkdir(parents=True, exist_ok=True)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        rc = _run_cli(
            [
                "feed",
                "--input",
                hidden_name,
                "--snapshot",
                str(SNAPSHOT_PATH),
                "--ports",
                str(PORTS),
            ],
            env=env,
        )
        assert rc.returncode == 0, rc.stderr
        rc2 = _run_cli(
            [
                "atlas",
                "--output",
                str(ATLAS),
                "--snapshot",
                str(SNAPSHOT_PATH),
                "--ports",
                str(PORTS),
            ],
            env=env,
        )
        assert rc2.returncode == 0, rc2.stderr
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(HIDDEN / hidden_name, PORTS)
    assert got["voyage_legs"] == ref["voyage_legs"]
    assert got["anomalies"] == ref["anomalies"]
    assert got["leg_chain_digest"] == ref["leg_chain_digest"]


def test_t1469c8_ais_vts_leg_anomaly_fields_present() -> None:
    """Atlas includes all anomaly counters."""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    for field in (
        "impossible_speed",
        "duplicate_mmsi",
        "burst_duplicate",
        "out_of_order",
    ):
        assert field in got["anomalies"]
        assert isinstance(got["anomalies"][field], int)


def test_t1469c8_ais_vts_leg_voyage_legs_numeric_ordinal_sort() -> None:
    """Atlas voyage_legs sorted by mmsi then numeric leg ordinal."""
    stream = STREAMS / "004-draught-boundary.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    keys = [(leg["mmsi"], _leg_ordinal(leg["leg_id"])) for leg in got["voyage_legs"]]
    assert keys == sorted(keys)
    assert keys == sorted(
        [(leg["mmsi"], _leg_ordinal(leg["leg_id"])) for leg in got["voyage_legs"]]
    )


def test_t1469c8_ais_vts_leg_snapshot_point_sort_order() -> None:
    """snapshot points sorted by mmsi, ts_epoch, seq."""
    stream = STREAMS / "005-burst-dedupe.jsonl"
    _feed_atlas(stream)
    snap_doc = json.loads(SNAPSHOT_PATH.read_text())
    keys = [(p["mmsi"], p["ts_epoch"], p["seq"]) for p in snap_doc["points"]]
    assert keys == sorted(keys)


def test_t1469c8_ais_vts_leg_leg_chain_digest_stable() -> None:
    """leg_chain_digest is sha256 of comma-joined leg ids."""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert got["leg_chain_digest"] == ref["leg_chain_digest"]


def test_t1469c8_ais_vts_leg_burst_anomaly_count() -> None:
    """Atlas anomalies.burst_duplicate matches burst removals."""
    stream = STREAMS / "005-burst-dedupe.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert got["anomalies"]["burst_duplicate"] == ref["anomalies"]["burst_duplicate"]
    assert got["anomalies"]["burst_duplicate"] >= 1


def test_t1469c8_ais_vts_leg_burst_keeps_lowest_seq() -> None:
    """Burst collapse retains the lowest seq when a higher seq arrives first."""
    stream = STREAMS / "005-burst-dedupe.jsonl"
    _feed_atlas(stream)
    snap_doc = json.loads(SNAPSHOT_PATH.read_text())
    ref_snap, _ = reference_pipeline(stream, PORTS)
    kept_seqs = {p["seq"] for p in snap_doc["points"]}
    assert 0 in kept_seqs
    assert 1 not in kept_seqs
    assert snap_doc["points"] == ref_snap["points"]


def test_t1469c8_ais_vts_leg_burst_collapse_snapshot() -> None:
    """Burst collapse runs during feed per burst-dedupe.md."""
    stream = STREAMS / "005-burst-dedupe.jsonl"
    _feed_atlas(stream)
    snap_doc = json.loads(SNAPSHOT_PATH.read_text())
    ref_snap, _ = reference_pipeline(stream, PORTS)
    assert (
        snap_doc["feed_stats"]["after_burst"] == ref_snap["feed_stats"]["after_burst"]
    )
    assert snap_doc["points"] == ref_snap["points"]


def test_t1469c8_ais_vts_leg_draught_boundary_splits_legs() -> None:
    """Draught delta threshold opens a new voyage leg."""
    stream = STREAMS / "004-draught-boundary.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert len(got["voyage_legs"]) == len(ref["voyage_legs"]) >= 2
    assert got["voyage_legs"] == ref["voyage_legs"]


def test_t1469c8_ais_vts_leg_speed_anomaly_suppression() -> None:
    """Impossible-speed points are suppressed during atlas."""
    stream = STREAMS / "003-speed-anomaly.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert got["anomalies"]["impossible_speed"] == ref["anomalies"]["impossible_speed"]
    assert got["anomalies"]["impossible_speed"] >= 1
    assert got["voyage_legs"] == ref["voyage_legs"]


def test_t1469c8_ais_vts_leg_mmsi_dedupe_anomaly_count() -> None:
    """Atlas anomalies.duplicate_mmsi matches feed dedupe removals."""
    stream = STREAMS / "002-mmsi-dedupe.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert got["anomalies"]["duplicate_mmsi"] == ref["anomalies"]["duplicate_mmsi"]
    assert got["anomalies"]["duplicate_mmsi"] >= 1


def test_t1469c8_ais_vts_leg_mmsi_keeps_lowest_seq() -> None:
    """MMSI dedupe keeps lowest seq when a higher-seq duplicate arrives first."""
    stream = STREAMS / "002-mmsi-dedupe.jsonl"
    _feed_atlas(stream)
    snap_doc = json.loads(SNAPSHOT_PATH.read_text())
    ref_snap, _ = reference_pipeline(stream, PORTS)
    kept_seqs = {p["seq"] for p in snap_doc["points"]}
    assert 0 in kept_seqs
    assert 1 not in kept_seqs
    assert snap_doc["points"] == ref_snap["points"]


def test_t1469c8_ais_vts_leg_mmsi_collapse_snapshot_counts() -> None:
    """MMSI dedupe removes duplicate coordinates within dedupe window."""
    stream = STREAMS / "002-mmsi-dedupe.jsonl"
    _feed_atlas(stream)
    snap_doc = json.loads(SNAPSHOT_PATH.read_text())
    ref_snap, _ = reference_pipeline(stream, PORTS)
    assert (
        snap_doc["feed_stats"]["after_mmsi_dedupe"]
        == ref_snap["feed_stats"]["after_mmsi_dedupe"]
    )
    assert (
        snap_doc["feed_stats"]["after_mmsi_dedupe"] < snap_doc["feed_stats"]["raw_rows"]
    )


def test_t1469c8_ais_vts_leg_port_entry_voyage_legs() -> None:
    """Port polygon entry splits voyage legs per voyage-leg-rules.md."""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    got = json.loads(ATLAS.read_text())
    _, ref = reference_pipeline(stream, PORTS)
    assert got["voyage_legs"] == ref["voyage_legs"]
    assert len(got["voyage_legs"]) >= 2
    assert got["voyage_legs"][0]["end_port"] in {"none", "rotterdam"}
    assert any(
        leg["start_port"] == "rotterdam" or leg["end_port"] == "rotterdam"
        for leg in got["voyage_legs"]
    )


def test_t1469c8_ais_vts_leg_snapshot_ts_epoch_codec() -> None:
    """Intake snapshot must store RFC3339-derived ts_epoch per ais-stream-format.md."""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    snap_doc = json.loads(SNAPSHOT_PATH.read_text())
    ref_snap, _ = reference_pipeline(stream, PORTS)
    assert snap_doc["feed_stats"] == ref_snap["feed_stats"]
    assert len(snap_doc["points"]) == len(ref_snap["points"])
    for got, exp in zip(snap_doc["points"], ref_snap["points"], strict=True):
        assert got["ts_epoch"] == exp["ts_epoch"]
        assert got["seq"] == exp["seq"]


def test_t1469c8_ais_vts_leg_all_bundled_streams_match_reference() -> None:
    """Every documented bundled stream case matches independent reference atlas."""
    for name in sorted(PROT_SHA):
        stream = STREAMS / name
        _feed_atlas(stream)
        got = json.loads(ATLAS.read_text())
        snap = json.loads(SNAPSHOT_PATH.read_text())
        ref_snap, ref_atlas = reference_pipeline(stream, PORTS)
        assert snap["feed_stats"] == ref_snap["feed_stats"], name
        assert snap["points"] == ref_snap["points"], name
        assert got == ref_atlas, name


def test_t1469c8_ais_vts_leg_bundled_stream_fingerprints() -> None:
    """Bundled streams under /app/fixtures/streams must match fixed SHA-256 digests."""
    on_disk = sorted(p.name for p in STREAMS.glob("*.jsonl"))
    assert on_disk == sorted(PROT_SHA)
    for name, digest in PROT_SHA.items():
        got = hashlib.sha256((STREAMS / name).read_bytes()).hexdigest()
        assert got == digest, f"fixture {name} was modified"
    ports_digest = hashlib.sha256(PORTS.read_bytes()).hexdigest()
    assert ports_digest == PORTS_SHA
    for name, digest in HIDDEN_SHA.items():
        path = HIDDEN / name
        assert path.is_file(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_t1469c8_ais_vts_leg_cli_binary_ready() -> None:
    """Verify aissegment was rebuilt before pytest."""
    assert BIN.is_file(), f"missing binary {BIN}"


def test_t1469c8_ais_vts_leg_voyage_json_written() -> None:
    """Atlas writes voyage atlas JSON to /app/output/voyage-atlas.json"""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    assert ATLAS.is_file(), "missing /app/output/voyage-atlas.json"
    payload = json.loads(ATLAS.read_text())
    assert "voyage_legs" in payload
    assert "leg_chain_digest" in payload


def test_t1469c8_ais_vts_leg_wal_snapshot_emitted() -> None:
    """Feed writes track snapshot JSON to /app/state/track-snapshot.json"""
    stream = STREAMS / "001-port-entry.jsonl"
    _feed_atlas(stream)
    assert SNAPSHOT_PATH.is_file(), "missing /app/state/track-snapshot.json"
    payload = json.loads(SNAPSHOT_PATH.read_text())
    assert payload["points"]
