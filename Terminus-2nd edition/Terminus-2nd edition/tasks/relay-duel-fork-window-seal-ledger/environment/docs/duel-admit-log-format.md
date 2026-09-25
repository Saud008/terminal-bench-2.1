# duel admit-log format

Files use extension .duellog as JSONL. Each line:

ts_ms (int), direction (in|out), method (CHALLENGE|ACK|FORFEIT|RESIGN|empty), duel_id (string), lane_tag (string), fork_tag (string), cseq (int), status (int, 0 for requests), branch_id (string optional).

Requests use method field. Responses use empty method and status code in status field.

Admit-log lines sort by ascending (ts_ms, cseq) lexicographic key after load.
