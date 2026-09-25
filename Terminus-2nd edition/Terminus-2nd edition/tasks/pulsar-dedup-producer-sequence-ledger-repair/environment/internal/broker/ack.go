package broker

import (
	"encoding/json"
	"os"

	"github.com/terminus/pulsar-dedup-replay/internal/model"
)

const brokerStatePath = "/app/state/broker-ledger.json"

type brokerFile struct {
	AckedMax map[string]int64 `json:"acked_max"`
}

func LoadAckedMax() (map[string]int64, error) {
	raw, err := os.ReadFile(brokerStatePath)
	if err != nil {
		return map[string]int64{}, nil
	}
	var bf brokerFile
	if err := json.Unmarshal(raw, &bf); err != nil {
		return nil, err
	}
	if bf.AckedMax == nil {
		return map[string]int64{}, nil
	}
	return bf.AckedMax, nil
}

func PersistAckedMax(acked map[string]int64) error {
	bf := brokerFile{AckedMax: acked}
	raw, err := json.MarshalIndent(bf, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(brokerStatePath, append(raw, '\n'), 0o644)
}

// MergeAck updates broker ack max from snapshot stats before export barrier.
func MergeAck(stats map[string]model.StreamStats) map[string]int64 {
	out := make(map[string]int64, len(stats))
	for k, st := range stats {
		out[k] = st.HighWater
	}
	return out
}
