"""Telemetry decoy — must stay off the replay/merge/export path."""


def wrap_noop(payload: dict) -> dict:
    return payload
