package atlaswriter

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

type GrantBalance struct {
	GrantID        string `json:"grant_id"`
	SpentCents     int64  `json:"spent_cents"`
	RemainingCents int64  `json:"remaining_cents"`
}

type Rejection struct {
	ExpenseID string `json:"expense_id"`
	Reason    string `json:"reason"`
}

type Atlas struct {
	GrantBalances []GrantBalance `json:"grant_balances"`
	Rejections    []Rejection    `json:"rejections"`
	AtlasDigest   string         `json:"atlas_digest"`
	AmendmentPass int            `json:"amendment_pass"`
}

func Publish(db *sql.DB, amendmentPass int) (Atlas, error) {
	runID := time.Now().UTC().Format(time.RFC3339Nano)
	rows, err := db.Query(`SELECT grant_id, spent_cents, remaining_cents FROM staged_balances ORDER BY grant_id`)
	if err != nil {
		return Atlas{}, err
	}
	var balances []GrantBalance
	for rows.Next() {
		var row GrantBalance
		if err := rows.Scan(&row.GrantID, &row.SpentCents, &row.RemainingCents); err != nil {
			_ = rows.Close()
			return Atlas{}, err
		}
		balances = append(balances, row)
	}
	if err := rows.Close(); err != nil {
		return Atlas{}, err
	}
	if err := rows.Err(); err != nil {
		return Atlas{}, err
	}

	for _, row := range balances {
		if _, err := db.Exec(
			`INSERT INTO published_spend(run_id, grant_id, spent_cents) VALUES(?, ?, ?)`,
			runID, row.GrantID, row.SpentCents,
		); err != nil {
			return Atlas{}, err
		}
	}

	rejRows, err := db.Query(`SELECT expense_id, reason FROM staged_rejections ORDER BY expense_id`)
	if err != nil {
		return Atlas{}, err
	}
	rejections := []Rejection{}
	for rejRows.Next() {
		var r Rejection
		if err := rejRows.Scan(&r.ExpenseID, &r.Reason); err != nil {
			_ = rejRows.Close()
			return Atlas{}, err
		}
		rejections = append(rejections, r)
	}
	if err := rejRows.Close(); err != nil {
		return Atlas{}, err
	}
	if err := rejRows.Err(); err != nil {
		return Atlas{}, err
	}

	digestSrc, _ := json.Marshal(struct {
		GrantBalances []GrantBalance `json:"grant_balances"`
		Rejections    []Rejection    `json:"rejections"`
		Pass          int            `json:"amendment_pass"`
	}{
		GrantBalances: balances,
		Rejections:    rejections,
		Pass:          amendmentPass,
	})
	sum := sha256.Sum256(digestSrc)
	atlas := Atlas{
		GrantBalances: balances,
		Rejections:    rejections,
		AtlasDigest:   hex.EncodeToString(sum[:]),
		AmendmentPass: amendmentPass,
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return Atlas{}, err
	}
	outPath := filepath.Clean("/app/output/spend-atlas.json")
	body, _ := json.MarshalIndent(atlas, "", "  ")
	body = append(body, '\n')
	if err := os.WriteFile(outPath, body, 0o644); err != nil {
		return Atlas{}, err
	}
	return atlas, nil
}
