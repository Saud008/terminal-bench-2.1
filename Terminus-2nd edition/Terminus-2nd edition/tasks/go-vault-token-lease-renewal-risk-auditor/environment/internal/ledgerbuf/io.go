package ledgerbuf

import (
	"bufio"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/vaultaud/internal/model"
)

// Write sorts by renewal_seq then token_id and emits one compact JSON object per line.
func Write(path string, rows []model.StagedLease) error {
	sort.SliceStable(rows, func(i, j int) bool {
		if rows[i].RenewalSeq != rows[j].RenewalSeq {
			return rows[i].RenewalSeq < rows[j].RenewalSeq
		}
		return rows[i].TokenID < rows[j].TokenID
	})
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	bw := bufio.NewWriter(f)
	for _, row := range rows {
		b, err := json.Marshal(row)
		if err != nil {
			return err
		}
		if _, err := bw.Write(b); err != nil {
			return err
		}
		if err := bw.WriteByte('\n'); err != nil {
			return err
		}
	}
	return bw.Flush()
}

// Read loads a staging ledger written by Write.
func Read(path string) ([]model.StagedLease, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []model.StagedLease
	for _, line := range splitLines(string(raw)) {
		if line == "" {
			continue
		}
		var row model.StagedLease
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return nil, err
		}
		out = append(out, row)
	}
	return out, nil
}

func splitLines(s string) []string {
	var lines []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			lines = append(lines, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		lines = append(lines, s[start:])
	}
	return lines
}
