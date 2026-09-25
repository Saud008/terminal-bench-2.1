package slotledger

import (
	"encoding/json"
	"os"
)

type Event struct {
	Stage  string         `json:"stage"`
	Detail map[string]any `json:"detail"`
}

func Append(stage string, detail map[string]any) error {
	if err := os.MkdirAll("/app/intermediate", 0o755); err != nil {
		return err
	}
	ev := Event{Stage: stage, Detail: detail}
	raw, err := json.Marshal(ev)
	if err != nil {
		return err
	}
	f, err := os.OpenFile("/app/intermediate/mpiq.slot-trace.ndjson", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(append(raw, '\n'))
	return err
}
