# Disconnect / Adapter-Power Capture Ordering

The adapter power state is a single global value, initialized to `on` at the
start of every absorb run and updated only by `adapter_power` operations.

A `disconnect` operation's ledger row and its entry in `disconnect_reasons`
must record the adapter power value **as it stood at the moment the
disconnect operation is processed**, following strict trace `(seq, ts)`
order. An `adapter_power` operation that appears later in the trace than a
`disconnect` must not influence that earlier disconnect's recorded power
value — absorb must process every operation in the trace's own order, and
must not reorder any operation class ahead of the rest of the trace.

For example, given:

```
{"seq":1,...,"op":"disconnect","mac":"AA:...","reason":"link_loss"}
{"seq":2,...,"op":"adapter_power","state":"off"}
```

the disconnect row must record `"adapter_power": "on"` (the power state in
effect at `seq:1`), not `"off"`.
