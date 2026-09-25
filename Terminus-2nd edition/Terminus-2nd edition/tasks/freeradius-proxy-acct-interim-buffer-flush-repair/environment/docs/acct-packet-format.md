# Accounting packet JSONL format

Each line is one JSON object:

- ts: integer epoch seconds when the proxy received the packet
- seq: monotonic capture sequence number (unique per line in a file)
- nas_id: NAS identifier string
- acct_status_type: Start, Interim-Update, or Stop
- attrs: map of RADIUS attribute names to values

Required attrs for all accounting types: Acct-Session-Id, Acct-Unique-Session-Id.

Start should include Session-Timeout and/or Acct-Interim-Interval when present in captures. Interim-Update and Stop include Acct-Input-Octets, Acct-Output-Octets, and Acct-Session-Time as integers.

Optional attrs: NAS-Reboot (boolean) on Start when the NAS rebooted.

Lines are processed in file sort order, then line order within each file.
