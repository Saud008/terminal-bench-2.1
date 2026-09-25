# FIX stream format — host-local drop-copy admission

On this system-administration drop-copy control plane, scenario manifests under the active fixture root (`/app/fixtures` or `--fixture-dir`) list JSONL stream files under `scenarios/<scenario>.json`. Each JSONL row contains session, msg_seq, sending_time, and fix_body.

fix_body uses pipe delimiters in fixtures. ingest converts pipes to SOH bytes before checksum validation and staging. Only MsgType 35=8 execution reports and 35=A logon rows with ResetSeqNumFlag 141=Y are replayed into staging events.

Required execution tags: 11 ClOrdID, 17 ExecID, 55 Symbol, 54 Side, 32 LastQty, 31 LastPx, 52 SendingTime, 34 MsgSeqNum, 20 ExecTransType, 150 ExecType. Optional 41 OrigClOrdID for cancel, correct, and bust chains.

When `TB3_SEQ_BIAS` is set to an integer at ingest time, that offset is added to each stream row's `msg_seq` before staging.

Staging writes `/app/state/dropcopy-stage.json` with at least:

- `scenario`: scenario id string
- `event_count`: integer equal to `len(events)`
- `events`: array sorted by `sending_time` ascending, then `msg_seq` ascending
- `replay_generation`: integer `0` after ingest (before any successful replay)
- each event may set `reset_seq` true when sourced from a 35=A / 141=Y logon
