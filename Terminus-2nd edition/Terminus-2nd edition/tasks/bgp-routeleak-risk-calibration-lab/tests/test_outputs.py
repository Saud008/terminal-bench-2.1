"""Black-box contract tests for BGP route-leak evaluation."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from routeleak_contract_math import (
    assign_splits,
    audit_digest,
    brier_score,
    ece_score,
    expected_report,
    extract_features,
    is_private,
    is_reserved,
    reference_eval,
    select_threshold,
    sigmoid,
)
from routeleak_support import FIXTURES, HIDDEN, evaluate, read_json, rebuild, reset

PUBLIC_EXPERIMENTS = (
    "basic-leak",
    "group-holdout",
    "peer-transit",
    "private-origin",
    "reserved-hop",
    "threshold-edge",
    "valley-path",
)


def assert_report_matches(actual: dict[str, object], expected: dict[str, object]) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if isinstance(expected_value, float):
            assert actual_value == pytest.approx(expected_value, abs=1e-9), key
        else:
            assert actual_value == expected_value, key


def test_cli_is_present(tmp_path: Path) -> None:
    """Feature-eval CLI must run evaluate successfully for a bundled batch."""
    completed = evaluate("basic-leak", tmp_path / "cli-present.json")
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("experiment", PUBLIC_EXPERIMENTS)
def test_public_experiment_matches_reference(experiment: str, tmp_path: Path) -> None:
    """Bundled experiment model-card matches independent reference_eval atlas."""
    reset()
    report_path = tmp_path / f"{experiment}.json"
    completed = evaluate(experiment, report_path, run_id="public-contract")
    assert completed.returncode == 0, completed.stderr
    assert_report_matches(
        read_json(report_path),
        reference_eval(FIXTURES / experiment, experiment=experiment, run_id="public-contract"),
    )


def test_default_report_and_snapshot_paths() -> None:
    # Ingest/export probe: the CLI must stage before exporting the sealed report.
    reset()
    completed = evaluate("basic-leak")
    assert completed.returncode == 0, completed.stderr
    report = read_json(Path("/app/output/routeleak_eval_report.json"))
    snapshot = read_json(Path("/app/state/eval-snapshot.json"))
    assert snapshot["experiment"] == report["experiment"] == "basic-leak"
    assert snapshot["selected_threshold"] == report["selected_threshold"]
    assert audit_digest(snapshot["rows"]) == report["audit_digest"]


def test_origin_uses_last_asn() -> None:
    """aspath-feature-vector.md: origin_asn uses the last ASN."""
    assert extract_features({"as_path": [64512, 64497], "peer_group": "a"}, {})[1] == 64497.0


def test_private_range_is_rfc1918_like_range() -> None:
    """aspath-feature-vector.md: private origins are 64512-65534."""
    assert is_private(64512) and is_private(65534)
    assert not is_private(64511) and not is_private(65535)


def test_reserved_range_is_documentation_range() -> None:
    """aspath-feature-vector.md: reserved hops are 64496-64511."""
    assert is_reserved(64496) and is_reserved(64511)
    assert not is_reserved(64512) and not is_reserved(64495)


def test_valley_is_provider_then_customer() -> None:
    """relationship-features.md: valley counts provider then customer hops."""
    features = extract_features(
        {"as_path": [1, 2, 3], "peer_group": "a"},
        {"1|2": "provider", "2|3": "customer"},
    )
    assert features[5] == 1.0


def test_group_split_is_sorted_and_cohesive() -> None:
    """group-holdout-split.md: sorted peer_group roles stay cohesive."""
    examples = [
        {"peer_group": "z"},
        {"peer_group": "a"},
        {"peer_group": "m"},
        {"peer_group": "z"},
    ]
    assert assign_splits(examples) == ["test", "train", "validation", "test"]


def test_threshold_is_inclusive_and_prefers_lower_tie() -> None:
    """fbeta-threshold-search.md: inclusive positives and lower-threshold ties."""
    threshold, value = select_threshold([0.10, 0.10], [1, 0])
    assert threshold == pytest.approx(0.05)
    assert value > 0


def test_stable_sigmoid_handles_extreme_logits() -> None:
    """stable-sigmoid.md: extreme logits remain finite probabilities."""
    assert sigmoid(1000.0) == pytest.approx(1.0)
    assert sigmoid(-1000.0) == pytest.approx(0.0)
    assert sigmoid(0.0) == pytest.approx(0.5)


def test_brier_is_squared_error() -> None:
    """confusion-brier-ece.md: Brier uses squared error."""
    assert brier_score([0.0, 0.5], [1, 0]) == pytest.approx(0.625)


def test_ece_is_count_weighted_ten_bin_value() -> None:
    """confusion-brier-ece.md: ECE is count-weighted across 10 bins."""
    assert ece_score([0.05, 0.15, 0.15], [0, 1, 0]) == pytest.approx(0.25)


def test_tb3_feature_scale_overrides_config(tmp_path: Path) -> None:
    """TB3_FEATURE_SCALE multiplies standardized features before inference."""
    reset()
    report_path = tmp_path / "scaled.json"
    completed = evaluate(
        "basic-leak",
        report_path,
        env={"TB3_FEATURE_SCALE": "1.75"},
    )
    assert completed.returncode == 0, completed.stderr
    assert_report_matches(
        read_json(report_path),
        expected_report(FIXTURES / "basic-leak", feature_scale=1.75),
    )


def test_usage_exit_is_one() -> None:
    """cli-exits.md: unknown subcommand exits 1."""
    completed = subprocess.run(
        ["routeleaklab", "not-a-verb"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1


def test_missing_experiment_exit_is_two(tmp_path: Path) -> None:
    """cli-exits.md: missing experiment directory exits 2."""
    completed = evaluate("does-not-exist", tmp_path / "unused.json")
    assert completed.returncode == 2


def test_hidden_extreme_logit_trap(tmp_path: Path) -> None:
    """Hidden /opt/verifier-fixtures/routeleaklab extreme-logit batch matches reference atlas."""
    reset()
    experiment = "hidden-extreme-logit"
    report_path = tmp_path / f"{experiment}.json"
    destination = FIXTURES / experiment
    shutil.copytree(HIDDEN / experiment, destination)
    try:
        completed = evaluate(experiment, report_path)
        assert completed.returncode == 0, completed.stderr
        assert_report_matches(read_json(report_path), expected_report(HIDDEN / experiment))
    finally:
        shutil.rmtree(destination)


def test_hidden_group_holdout_trap(tmp_path: Path) -> None:
    """Hidden /opt/verifier-fixtures/routeleaklab grouped holdout matches reference atlas."""
    reset()
    experiment = "hidden-group-holdout"
    report_path = tmp_path / f"{experiment}.json"
    destination = FIXTURES / experiment
    shutil.copytree(HIDDEN / experiment, destination)
    try:
        completed = evaluate(experiment, report_path, env={"TB3_FEATURE_SCALE": "1.0"})
        assert completed.returncode == 0, completed.stderr
        assert_report_matches(read_json(report_path), expected_report(HIDDEN / experiment))
    finally:
        shutil.rmtree(destination)


def test_rebuild_helper_restores_cli(tmp_path: Path) -> None:
    """Verifier rebuild helper must restore routeleaklab after source patches."""
    rebuild()
    completed = evaluate("basic-leak", tmp_path / "rebuilt.json")
    assert completed.returncode == 0, completed.stderr


def test_selected_threshold_matches_reference(tmp_path: Path) -> None:
    """Model-card selected_threshold matches independent calibration math."""
    reset()
    report_path = tmp_path / "threshold.json"
    completed = evaluate("threshold-edge", report_path)
    assert completed.returncode == 0, completed.stderr
    actual = read_json(report_path)
    expected = expected_report(FIXTURES / "threshold-edge")
    assert actual["selected_threshold"] == pytest.approx(expected["selected_threshold"])
    assert actual["validation_fbeta"] == pytest.approx(expected["validation_fbeta"], abs=1e-9)
