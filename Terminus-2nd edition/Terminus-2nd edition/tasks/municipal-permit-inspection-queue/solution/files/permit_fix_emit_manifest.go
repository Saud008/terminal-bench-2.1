package manifestemit

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/mpiqctl/internal/bundleload"
	"github.com/terminus/mpiqctl/internal/permitstore"
)

func PublishQueue(scenario, outPath string) error {
	if err := bundleload.BundleLoaded(scenario); err != nil {
		return err
	}
	pass, err := readQueuePass()
	if err != nil {
		return err
	}
	if pass <= 0 {
		return fmt.Errorf("queue_pass must be positive")
	}
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	epoch, err := metaInt(db, "planning_epoch_day")
	if err != nil {
		return err
	}
	entries, holdSummary, err := fetchQueue(db)
	if err != nil {
		return err
	}
	entryRaw, err := json.Marshal(entries)
	if err != nil {
		return err
	}
	digest := sha256.Sum256(entryRaw)
	body := map[string]any{
		"scenario":            scenario,
		"planning_epoch_day": epoch,
		"queue_entries":       entries,
		"hold_summary":        holdSummary,
		"queue_digest":        hex.EncodeToString(digest[:]),
	}
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	path := outPath
	if path == "" {
		path = "/app/output/permit-queue-manifest.json"
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}

func fetchQueue(db *sql.DB) ([]map[string]any, map[string]int, error) {
	rs, err := db.Query(`SELECT permit_id,inspector_id,scheduled_day,inspection_lane,status FROM queue_entries ORDER BY permit_id`)
	if err != nil {
		return nil, nil, err
	}
	defer rs.Close()
	rows := make([]map[string]any, 0)
	for rs.Next() {
		var pid, iid, lane, status string
		var day int
		if err := rs.Scan(&pid, &iid, &day, &lane, &status); err != nil {
			return nil, nil, err
		}
		rows = append(rows, map[string]any{
			"permit_id": pid, "inspector_id": iid, "scheduled_day": day,
			"inspection_lane": lane, "status": status,
		})
	}
	sort.Slice(rows, func(i, j int) bool {
		return rows[i]["permit_id"].(string) < rows[j]["permit_id"].(string)
	})
	holdSummary := map[string]int{}
	hrs, err := db.Query(`SELECT p.district_id, COUNT(*) FROM queue_scores s JOIN permits p ON s.permit_id=p.permit_id WHERE s.hold_blocked=1 GROUP BY p.district_id`)
	if err == nil {
		defer hrs.Close()
		for hrs.Next() {
			var d string
			var c int
			if err := hrs.Scan(&d, &c); err != nil {
				break
			}
			holdSummary[d] = c
		}
	}
	return rows, holdSummary, rs.Err()
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

func readQueuePass() (int, error) {
	raw, err := os.ReadFile("/app/state/queue-pass.json")
	if err != nil {
		return 0, err
	}
	var body struct {
		QueuePass int `json:"queue_pass"`
	}
	if err := json.Unmarshal(raw, &body); err != nil {
		return 0, err
	}
	return body.QueuePass, nil
}
