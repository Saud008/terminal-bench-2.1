package ingest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/feast-pit-join/internal/model"
)

func ScenarioPath(dir, name string) string {
	return filepath.Join(dir, name+".json")
}

func LoadScenario(path, seed string) (model.ScenarioFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.ScenarioFile{}, err
	}
	var sc model.ScenarioFile
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.ScenarioFile{}, err
	}
	return sc, nil
}

func Materialize(sc model.ScenarioFile, seed string) []model.MaterializedEvent {
	out := make([]model.MaterializedEvent, 0, len(sc.Events))
	for _, ev := range sc.Events {
		me := model.MaterializedEvent{
			EntityID:  scopedID(seed, ev.EntityBase),
			EventTS:   ev.EventTS,
			Feature:   ev.Feature,
			Value:     ev.Value,
			Source:    ev.Source,
			Partition: ev.Partition,
			Seq:       ev.Seq,
		}
		if ev.DeviceBase != "" {
			me.DeviceID = scopedID(seed, ev.DeviceBase)
		}
		if ev.SessionBase != "" {
			me.SessionID = scopedID(seed, ev.SessionBase)
		}
		out = append(out, me)
	}
	return out
}

func scopedID(seed, base string) string {
	h := hash8(seed + ":" + base)
	return fmt.Sprintf("%s-%s", base, h)
}

func hash8(s string) string {
	var x uint32 = 2166136261
	for i := 0; i < len(s); i++ {
		x ^= uint32(s[i])
		x *= 16777619
	}
	return fmt.Sprintf("%08x", x)
}
