# SIP transcript format

Files use extension .siplog as JSONL. Each line:

ts_ms (int), direction (in|out), method (INVITE|ACK|CANCEL|BYE|empty), call_id (string), from_tag (string), to_tag (string), cseq (int), status (int, 0 for requests), branch_id (string optional).

Requests use method field. Responses use empty method and status code in status field.

Transcript lines sort by ascending (ts_ms, cseq) lexicographic key after load.
