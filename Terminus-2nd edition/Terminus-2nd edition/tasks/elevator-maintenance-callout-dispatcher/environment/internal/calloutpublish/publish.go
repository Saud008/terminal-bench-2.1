package calloutpublish

// PublishRoster writes /app/output/callout-roster.json after bind-roster completes.

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/calloutd/internal/rosterfeed"
	"github.com/terminus/calloutd/internal/store"
)

func PublishRoster(scenario, outPath string) error {
	if err := rosterfeed.BundleLoaded(scenario); err != nil {
		return err
	}
	pass, err := readCalloutPass()
	if err != nil {
		return err
	}
	if pass <= 0 {
		return fmt.Errorf("callout_pass must be positive")
	}
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	anchor, err := metaInt(db, "roster_epoch_minute")
	if err != nil {
		return err
	}
	assignments, err := fetchAssignments(db)
	if err != nil {
		return err
	}
	assignRaw, err := json.Marshal(assignments)
	if err != nil {
		return err
	}
	digest := sha256.Sum256(assignRaw)
	body := map[string]any{
		"scenario":              scenario,
		"roster_epoch_minute": anchor,
		"assignments":             assignments,
		"roster_digest":       hex.EncodeToString(digest[:]),
	}
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	path := outPath
	if path == "" {
		path = "/app/output/callout-roster.json"
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}

func fetchAssignments(db *sql.DB) ([]map[string]any, error) {
	rs, err := db.Query(`SELECT fault_id,tech_id,planned_minute,status FROM assignments ORDER BY fault_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var rows []map[string]any
	for rs.Next() {
		var faultID, techID, status string
		var planned int
		if err := rs.Scan(&faultID, &techID, &planned, &status); err != nil {
			return nil, err
		}
		rows = append(rows, map[string]any{
			"fault_id": faultID, "tech_id": techID, "planned_minute": planned, "status": status,
		})
	}
	sort.Slice(rows, func(i, j int) bool {
		return rows[i]["fault_id"].(string) < rows[j]["fault_id"].(string)
	})
	return rows, nil
}

func metaInt(db *sql.DB, key string) (int, error) {
	raw, err := store.GetMeta(db, key)
	if err != nil {
		return 0, err
	}
	var v int
	if err := json.Unmarshal([]byte(raw), &v); err != nil {
		return 0, err
	}
	return v, nil
}

func readCalloutPass() (int, error) {
	raw, err := os.ReadFile("/app/state/callout-pass.json")
	if err != nil {
		return 0, err
	}
	var body struct {
		CalloutPass int `json:"callout_pass"`
	}
	if err := json.Unmarshal(raw, &body); err != nil {
		return 0, err
	}
	return body.CalloutPass, nil
}
