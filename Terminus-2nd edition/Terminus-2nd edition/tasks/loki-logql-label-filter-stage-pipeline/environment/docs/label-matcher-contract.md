# Label matcher contract

Matcher stages use the form {key="value",...}. Every selector key must equal the value in the log line labels map at ingest time.

Parsed json fields must never influence matcher filtering. Lines failing the matcher must not contribute to downstream unwrap or sum stages.
