# Version gate

Compare workflow handler versions as numeric semver tuples `(major, minor, patch)`. String ordering is invalid (`2.10.0` must be greater than `2.4.10`).

`GateOpen(handlerVersion, signalTargetVersion)` is true when the handler tuple is **greater than or equal to** the signal target tuple.
