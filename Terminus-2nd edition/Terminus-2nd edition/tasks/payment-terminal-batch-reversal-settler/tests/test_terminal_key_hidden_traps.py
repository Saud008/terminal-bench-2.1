"""Hidden overlay traps for terminal key salt and reversal ordering."""

from __future__ import annotations

from independent_pay_fsm import expected_bundle_payload, expected_hmac_witness
from pay_acquirer_exec import (
    OVERLAY_FIXTURES,
    PATH_BUNDLE,
    PATH_WITNESS,
    TERMSET_BIN,
    exec_termsetctl,
    flush_batch_state,
    read_json_object,
)


def test_overlay_salted_terminal_key_witness() -> None:
    """TB3 hmac-key-trap verifies salted terminal key witness binding."""
    flush_batch_state()
    env = {
        "TB3_FIXTURE_DIR": str(OVERLAY_FIXTURES),
        "TB3_TERMINAL_KEY_SALT": "tb3-salt",
    }
    for argv in (
        [TERMSET_BIN, "compile-journal", "--scenario", "hmac-key-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
        [TERMSET_BIN, "seal-bundle", "--scenario", "hmac-key-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
    ):
        proc = exec_termsetctl(argv, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    assert PATH_BUNDLE.as_posix() == "/app/output/settlement-bundle.json"
    witness = PATH_WITNESS.read_text(encoding="utf-8").strip()
    ref = expected_hmac_witness("hmac-key-trap", OVERLAY_FIXTURES)
    assert witness == ref


def test_overlay_reversal_before_sale_still_pairs() -> None:
    """TB3 reversal-order-trap pairs reversal listed before sale when sorted by event_ms."""
    flush_batch_state()
    env = {"TB3_FIXTURE_DIR": str(OVERLAY_FIXTURES)}
    exec_termsetctl(
        [TERMSET_BIN, "compile-journal", "--scenario", "reversal-order-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
        env=env,
    )
    exec_termsetctl(
        [TERMSET_BIN, "seal-bundle", "--scenario", "reversal-order-trap", "--fixture-dir", str(OVERLAY_FIXTURES)],
        env=env,
    )
    body = read_json_object(PATH_BUNDLE)
    ref = expected_bundle_payload("reversal-order-trap", OVERLAY_FIXTURES)
    assert body["net_amount_cents"] == ref["net_amount_cents"] == 0
    assert body["settled_count"] == ref["settled_count"] == 1
