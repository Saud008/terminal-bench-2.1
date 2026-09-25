package wireframe

import "encoding/json"

type AdmitDocument struct {
	ClientSeq int             `json:"client_seq"`
	Payload   json.RawMessage `json:"payload"`
}

type AdmitResult struct {
	ID          string `json:"_id"`
	ClientSeq   int    `json:"client_seq"`
	RepeatClaim bool   `json:"repeat_claim"`
}
