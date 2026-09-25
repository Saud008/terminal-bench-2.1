package ledger

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/borderdocctl/internal/store"
)

type ledgerLine struct {
	HolderID          string `json:"holder_id"`
	VisaID            string `json:"visa_id"`
	RemainingStayDays int    `json:"remaining_stay_days"`
	PassNum           int    `json:"pass_num"`
}

func PublishRows(scenario string, outPath string) error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()

	pass := readEvalPass()
	if pass <= 0 {
		return fmt.Errorf("eval_pass must be positive")
	}

	rows, err := db.Query(`SELECT holder_id, visa_id, remaining_stay_days FROM decisions ORDER BY holder_id, visa_id`)
	if err != nil {
		return err
	}
	defer rows.Close()

	var lines []ledgerLine
	for rows.Next() {
		var holder, visa string
		var rem int
		if err := rows.Scan(&holder, &visa, &rem); err != nil {
			return err
		}
		_, err := db.Exec(`INSERT INTO ledger(holder_id,visa_id,line_kind,amount_days,pass_num) VALUES(?,?,?,?,?)`,
			holder, visa, "validity", rem, pass)
		if err != nil {
			return err
		}
		lines = append(lines, ledgerLine{
			HolderID:          holder,
			VisaID:            visa,
			RemainingStayDays: rem,
			PassNum:           pass,
		})
	}
	if err := rows.Err(); err != nil {
		return err
	}

	sid, _ := store.GetMeta(db, "scenario_id")
	digest := digestLines(lines)
	rep := map[string]any{
		"scenario_id":   sid,
		"eval_pass":     pass,
		"ledger_rows":   lines,
		"ledger_digest": digest,
	}
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if outPath == "" {
		outPath = "/app/output/ledger-manifest.json"
	}
	return os.WriteFile(outPath, raw, 0o644)
}

func digestLines(lines []ledgerLine) string {
	raw, _ := json.Marshal(lines)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func readEvalPass() int {
	raw, err := os.ReadFile("/app/state/eval-pass.json")
	if err != nil {
		return 0
	}
	var body struct {
		EvalPass int `json:"eval_pass"`
	}
	if json.Unmarshal(raw, &body) != nil {
		return 0
	}
	return body.EvalPass
}

func CountLedger(db *sql.DB) (int, error) {
	var n int
	err := db.QueryRow(`SELECT COUNT(*) FROM ledger`).Scan(&n)
	return n, err
}
