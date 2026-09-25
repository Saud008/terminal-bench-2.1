# Intake batch

POST /v1/admit accepts documents containing client_seq and payload; X-Test-Now and X-Machine-Id
scope the mint clock and machine binding. The machine/client_seq pair is a uniqueness claim.
A repeated claim returns its original _id with the response flag set and must not overwrite the sealed payload.
