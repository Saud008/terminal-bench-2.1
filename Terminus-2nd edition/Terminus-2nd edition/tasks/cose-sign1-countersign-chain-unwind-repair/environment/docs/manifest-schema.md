# Chain manifest schema

Written by export to --manifest path.

{
  "ledger_rows": integer,
  "chains": [
    {
      "input_sha256": string hex,
      "outer_ok": boolean,
      "countersign_ok": boolean,
      "partial_retained": boolean,
      "unwind": [
        { "index": integer, "kid": string, "alg": integer, "verify_ok": boolean }
      ]
    }
  ]
}

partial_retained is true when outer_ok is true and countersign_ok is false (partial chain kept per countersign-unwind.md).

chains array order matches ledger ingest order (rowid ascending).

Re-export without new ingest must produce byte-identical manifest JSON (same spacing: pretty-print with 2-space indent, trailing newline).
