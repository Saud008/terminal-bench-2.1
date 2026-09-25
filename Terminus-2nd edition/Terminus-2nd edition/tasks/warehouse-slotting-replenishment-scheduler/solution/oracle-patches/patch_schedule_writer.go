package atlasemit

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/whslot/internal/replenledger"
	"github.com/terminus/whslot/internal/yardfeed"
)

func Publish(outPath string) error {
	if err := PassGate(); err != nil {
		return err
	}
	bundle, err := yardfeed.ReadActive()
	if err != nil {
		return err
	}
	db, err := replenledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	assignments, err := loadAssignments(db)
	if err != nil {
		return err
	}
	body := map[string]any{"wave_id": bundle.WaveID, "assignments": assignments}
	digest, err := digestBody(body)
	if err != nil {
		return err
	}
	body["atlas_fingerprint"] = digest
	raw, err := json.Marshal(body)
	if err != nil {
		return err
	}
	if outPath == "" {
		outPath = "/app/output/slot-replen-atlas.json"
	}
	return os.WriteFile(outPath, append(raw, '\n'), 0o644)
}

func loadAssignments(db *sql.DB) ([]map[string]any, error) {
	rs, err := db.Query(`SELECT task_key,sku_id,slot_id,units,start_minute,end_minute,worker_id FROM wave_tasks ORDER BY task_key`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var rows []map[string]any
	for rs.Next() {
		var key, sku, slot, worker string
		var units, start, end int
		if err := rs.Scan(&key, &sku, &slot, &units, &start, &end, &worker); err != nil {
			return nil, err
		}
		rows = append(rows, map[string]any{"task_key": key, "sku_id": sku, "slot_id": slot, "units": units, "start_minute": start, "end_minute": end, "worker_id": worker})
	}
	return rows, rs.Err()
}

func digestBody(body map[string]any) (string, error) {
	copy := map[string]any{"wave_id": body["wave_id"], "assignments": body["assignments"]}
	raw, err := json.Marshal(canonical(copy))
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:]), nil
}

func canonical(v any) any {
	switch t := v.(type) {
	case map[string]any:
		keys := make([]string, 0, len(t))
		for k := range t {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		out := make(map[string]any, len(t))
		for _, k := range keys {
			out[k] = canonical(t[k])
		}
		return out
	case []map[string]any:
		arr := make([]any, len(t))
		for i, row := range t {
			arr[i] = canonical(row)
		}
		return arr
	case []any:
		out := make([]any, len(t))
		for i, x := range t {
			out[i] = canonical(x)
		}
		return out
	default:
		return v
	}
}

func PassGate() error {
	raw, err := os.ReadFile("/app/state/wave-latch-pass.json")
	if err != nil {
		return err
	}
	var gate map[string]int
	if err := json.Unmarshal(raw, &gate); err != nil {
		return err
	}
	if gate["wave_latch_pass"] <= 0 {
		return fmt.Errorf("crew-bind required before publish")
	}
	return nil
}
