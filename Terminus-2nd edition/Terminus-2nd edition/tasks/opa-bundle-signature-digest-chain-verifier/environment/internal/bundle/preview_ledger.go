package bundle

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type PreviewEntry struct {
	Raw       string `json:"raw"`
	Canonical string `json:"canonical"`
}

type PreviewLedger struct {
	Bundle  string         `json:"bundle"`
	Order   []string       `json:"order"`
	Entries []PreviewEntry `json:"entries"`
}

const previewLedgerPath = "/app/state/preview-ledger.json"

// WritePreviewLedger persists import-preview using manifest declaration order
// (broken — contract requires UTF-8 lexicographic order).
func WritePreviewLedger(bundleDir string, members []Member, manifestOrder []string) error {
	entries := make([]PreviewEntry, 0, len(members))
	order := make([]string, 0, len(members))
	byRaw := make(map[string]Member, len(members))
	for _, m := range members {
		byRaw[m.Raw] = m
	}
	for _, raw := range manifestOrder {
		m, ok := byRaw[raw]
		if !ok {
			continue
		}
		if m.Canonical == "MANIFEST.json" || m.Canonical == ".signatures.json" {
			continue
		}
		entries = append(entries, PreviewEntry{Raw: m.Raw, Canonical: m.Canonical})
		order = append(order, m.Canonical)
	}
	ledger := PreviewLedger{Bundle: bundleDir, Order: order, Entries: entries}
	if err := os.MkdirAll(filepath.Dir(previewLedgerPath), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(ledger, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(previewLedgerPath, raw, 0o644)
}

func LoadPreviewLedger() (*PreviewLedger, error) {
	raw, err := os.ReadFile(previewLedgerPath)
	if err != nil {
		return nil, err
	}
	var ledger PreviewLedger
	if err := json.Unmarshal(raw, &ledger); err != nil {
		return nil, err
	}
	return &ledger, nil
}
