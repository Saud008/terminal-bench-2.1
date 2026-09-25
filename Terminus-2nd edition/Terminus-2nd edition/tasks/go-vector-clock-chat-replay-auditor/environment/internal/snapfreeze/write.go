package snapfreeze

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/vcreplay/internal/model"
)

const DefaultStagePath = "/app/state/chat-staging.json"

func WriteStage(path string, snap model.ChatStaging) error {
	if path == "" {
		path = DefaultStagePath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	digest, err := computeDigest(snap.Room, snap.Scenario, snap.Events)
	if err != nil {
		return err
	}
	snap.StagingDigest = digest
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadStage(path string) (model.ChatStaging, error) {
	if path == "" {
		path = DefaultStagePath
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.ChatStaging{}, err
	}
	var snap model.ChatStaging
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.ChatStaging{}, err
	}
	return snap, nil
}

func computeDigest(room, scenario string, events []model.StagedEvent) (string, error) {
	payload := map[string]any{
		"room":     room,
		"scenario": scenario,
		"events":   canonicalEvents(events),
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func canonicalEvents(events []model.StagedEvent) []map[string]any {
	out := make([]map[string]any, len(events))
	for i, ev := range events {
		vc := map[string]int{}
		for k, v := range ev.VectorClock {
			vc[k] = v
		}
		out[i] = map[string]any{
			"event_id":      ev.EventID,
			"payload":       ev.Payload,
			"sender":        ev.Sender,
			"timestamp_ms":  ev.TimestampMs,
			"type":          ev.Type,
			"vector_clock":  vc,
		}
	}
	return out
}
