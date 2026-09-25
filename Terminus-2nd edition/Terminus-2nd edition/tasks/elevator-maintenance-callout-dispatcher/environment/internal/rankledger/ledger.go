package rankledger

import (
	"encoding/json"
	"os"
)

// WriteRankLedger persists ranked fault ids for bind-roster audit rows.
func WriteRankLedger(rows []map[string]any) error {
	body := map[string]any{"ranked": rows}
	raw, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile("/app/work/rank-ledger.json", append(raw, '\n'), 0o644)
}
