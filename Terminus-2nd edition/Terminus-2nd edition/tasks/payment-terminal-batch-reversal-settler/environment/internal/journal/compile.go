package journal

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"

	"github.com/terminus/termsetctl/internal/model"
)

const JournalPath = "/app/state/batch-journal.jsonl"
const JournalMetaPath = "/app/state/journal-meta.json"

func lineDigest(batchID, terminalID, txnID, authNorm string, amount int64, state string) string {
	payload := strings.Join([]string{
		batchID,
		terminalID,
		txnID,
		authNorm,
		fmt.Sprintf("%d", amount),
		state,
	}, "|")
	sum := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(sum[:])
}

func SortRows(rows []model.NormalizedTxn) []model.NormalizedTxn {
	out := append([]model.NormalizedTxn(nil), rows...)
	sort.Slice(out, func(i, j int) bool {
		if out[i].EventMS != out[j].EventMS {
			return out[i].EventMS < out[j].EventMS
		}
		return out[i].TxnID < out[j].TxnID
	})
	return out
}

func AttachDigests(batchID string, lines []model.JournalLine, auth map[string]string) []model.JournalLine {
	out := make([]model.JournalLine, len(lines))
	for i, line := range lines {
		out[i] = line
		out[i].NormalizedDigest = lineDigest(batchID, line.TerminalID, line.TxnID, auth[line.TxnID], line.AmountCents, line.State)
	}
	return out
}

func JournalDigest(lines []model.JournalLine) string {
	var b strings.Builder
	for _, line := range lines {
		row, _ := json.Marshal(line)
		b.Write(row)
		b.WriteByte('\n')
	}
	sum := sha256.Sum256([]byte(b.String()))
	return hex.EncodeToString(sum[:])
}

func WriteJournal(scenario, batchID string, lines []model.JournalLine) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	f, err := os.Create(JournalPath)
	if err != nil {
		return err
	}
	defer f.Close()
	for _, line := range lines {
		row, err := json.Marshal(line)
		if err != nil {
			return err
		}
		if _, err := f.Write(append(row, '\n')); err != nil {
			return err
		}
	}
	meta := model.JournalFile{
		Engine:        "termsetctl",
		Scenario:      scenario,
		BatchID:       batchID,
		JournalDigest: JournalDigest(lines),
		LineCount:     len(lines),
	}
	raw, err := json.MarshalIndent(meta, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(JournalMetaPath, raw, 0o644)
}
