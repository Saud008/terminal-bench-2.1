"""Legacy telemetry shim unused by evaluate."""


def emit_gauge(name: str, value: float) -> None:
    _ = (name, value)
