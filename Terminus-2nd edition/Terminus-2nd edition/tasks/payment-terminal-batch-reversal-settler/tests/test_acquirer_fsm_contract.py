"""Payment FSM contract tests for reversal, cutoff, sequence, and seal behavior."""

from __future__ import annotations

from independent_pay_fsm import (
    expected_bundle_payload,
    expected_hmac_witness,
    expected_journal_header,
    expected_journal_rows,
)
from pay_acquirer_exec import (
    BUNDLED_FIXTURES,
    PATH_BUNDLE,
    PATH_JOURNAL,
    PATH_META,
    PATH_WITNESS,
    SCEN_CLEAN,
    SCEN_CUTOFF,
    SCEN_MULTI,
    SCEN_REPUBLISH,
    SCEN_REVERSAL,
    SCEN_SEQ,
    SCEN_STALE,
    flush_batch_state,
    read_json_object,
    read_jsonl_rows,
    run_settle_pipeline,
)


def test_merchant_batch_line_count_matches_fsm() -> None:
    """clean-settle includes every in-cutoff sale with global seq starting at 1."""
    flush_batch_state()
    run_settle_pipeline(SCEN_CLEAN)
    lines = read_jsonl_rows(PATH_JOURNAL)
    ref = expected_journal_rows(SCEN_CLEAN, BUNDLED_FIXTURES)
    assert len(lines) == len(ref) == 2
    assert [row["seq"] for row in lines] == [1, 2]


def test_chip_capture_net_amount_matches_reference() -> None:
    """clean-settle net_amount_cents sums settled sales per seal-hmac-contract."""
    flush_batch_state()
    run_settle_pipeline(SCEN_CLEAN)
    bundle = read_json_object(PATH_BUNDLE)
    ref = expected_bundle_payload(SCEN_CLEAN, BUNDLED_FIXTURES)
    assert bundle["net_amount_cents"] == ref["net_amount_cents"] == 3600


def test_linked_reversal_zeroes_batch_net() -> None:
    """reversal-pair applies linked reversal so net_amount_cents is zero."""
    flush_batch_state()
    run_settle_pipeline(SCEN_REVERSAL)
    bundle = read_json_object(PATH_BUNDLE)
    ref = expected_bundle_payload(SCEN_REVERSAL, BUNDLED_FIXTURES)
    assert bundle["net_amount_cents"] == ref["net_amount_cents"] == 0
    assert bundle["settled_count"] == ref["settled_count"] == 1


def test_cutoff_boundary_txn_included() -> None:
    """cutoff-window includes txn at cutoff_event_ms per cutoff-window-contract."""
    flush_batch_state()
    run_settle_pipeline(SCEN_CUTOFF)
    lines = read_jsonl_rows(PATH_JOURNAL)
    ref = expected_journal_rows(SCEN_CUTOFF, BUNDLED_FIXTURES)
    assert len(lines) == len(ref) == 1
    assert lines[0]["txn_id"] == ref[0]["txn_id"]


def test_cutoff_late_txn_excluded() -> None:
    """cutoff-window excludes txn strictly after cutoff_event_ms."""
    flush_batch_state()
    run_settle_pipeline(SCEN_CUTOFF)
    ids = {row["txn_id"] for row in read_jsonl_rows(PATH_JOURNAL)}
    ref_ids = {row["txn_id"] for row in expected_journal_rows(SCEN_CUTOFF, BUNDLED_FIXTURES)}
    assert ids == ref_ids
    assert len(ids) == 1


def test_global_sequence_counter_across_merchants() -> None:
    """seq-strict uses one global seq across merchants per batch-journal-contract."""
    flush_batch_state()
    run_settle_pipeline(SCEN_SEQ)
    lines = read_jsonl_rows(PATH_JOURNAL)
    ref = expected_journal_rows(SCEN_SEQ, BUNDLED_FIXTURES)
    assert [row["seq"] for row in lines] == [row["seq"] for row in ref] == [1, 2]


def test_journal_line_digest_includes_merchant() -> None:
    """Journal lines carry merchant-aware normalized_digest from batch-journal-contract."""
    flush_batch_state()
    run_settle_pipeline(SCEN_MULTI)
    lines = read_jsonl_rows(PATH_JOURNAL)
    ref = expected_journal_rows(SCEN_MULTI, BUNDLED_FIXTURES)
    assert lines[0]["normalized_digest"] == ref[0]["normalized_digest"]
    assert lines[1]["normalized_digest"] == ref[1]["normalized_digest"]


def test_settlement_bundle_schema_keys_present() -> None:
    """settlement-bundle.json exposes required seal-hmac-contract keys."""
    flush_batch_state()
    run_settle_pipeline(SCEN_MULTI)
    bundle = read_json_object(PATH_BUNDLE)
    for key in (
        "engine",
        "scenario",
        "batch_id",
        "terminal_key_id",
        "journal_digest",
        "net_amount_cents",
        "settled_count",
        "bundle_version",
    ):
        assert key in bundle


def test_witness_hmac_binds_journal_digest() -> None:
    """Witness HMAC is keyed over journal_digest not bundle JSON body."""
    flush_batch_state()
    run_settle_pipeline(SCEN_MULTI)
    witness = PATH_WITNESS.read_text(encoding="utf-8").strip()
    ref = expected_hmac_witness(SCEN_MULTI, BUNDLED_FIXTURES)
    assert witness == ref


def test_orphan_reversal_marked_rejected() -> None:
    """stale-reversal marks orphan reversal as reversal_rejected."""
    flush_batch_state()
    run_settle_pipeline(SCEN_STALE)
    lines = read_jsonl_rows(PATH_JOURNAL)
    ref = expected_journal_rows(SCEN_STALE, BUNDLED_FIXTURES)
    assert lines[0]["state"] == ref[0]["state"] == "reversal_rejected"
    bundle = read_json_object(PATH_BUNDLE)
    assert bundle["net_amount_cents"] == 0


def test_multi_merchant_net_total_sums_sales() -> None:
    """multi-merchant sums both settled sales into net_amount_cents."""
    flush_batch_state()
    run_settle_pipeline(SCEN_MULTI)
    bundle = read_json_object(PATH_BUNDLE)
    ref = expected_bundle_payload(SCEN_MULTI, BUNDLED_FIXTURES)
    assert bundle["net_amount_cents"] == ref["net_amount_cents"] == 3700


def test_journal_meta_digest_matches_lines() -> None:
    """journal-meta.json journal_digest matches recomputed reference digest."""
    flush_batch_state()
    run_settle_pipeline(SCEN_CLEAN)
    meta = read_json_object(PATH_META)
    ref = expected_journal_header(SCEN_CLEAN, BUNDLED_FIXTURES)
    assert meta["journal_digest"] == ref["journal_digest"]
    assert meta["line_count"] == ref["line_count"]


def test_republish_keeps_stable_journal_digest() -> None:
    """hmac-republish reproduces identical journal_digest on repeat seal."""
    flush_batch_state()
    run_settle_pipeline(SCEN_REPUBLISH)
    first = read_json_object(PATH_BUNDLE)["journal_digest"]
    run_settle_pipeline(SCEN_REPUBLISH)
    second = read_json_object(PATH_BUNDLE)["journal_digest"]
    ref = expected_bundle_payload(SCEN_REPUBLISH, BUNDLED_FIXTURES)["journal_digest"]
    assert first == second == ref


def test_auth_code_lowercase_before_digest() -> None:
    """Auth codes normalize to lowercase before digest per reversal-pairing-contract."""
    flush_batch_state()
    run_settle_pipeline(SCEN_CLEAN)
    lines = read_jsonl_rows(PATH_JOURNAL)
    ref = expected_journal_rows(SCEN_CLEAN, BUNDLED_FIXTURES)
    assert lines == ref
