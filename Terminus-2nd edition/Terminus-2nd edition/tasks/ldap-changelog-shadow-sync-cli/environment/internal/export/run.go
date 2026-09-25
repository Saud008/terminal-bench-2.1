package export

import (
	"encoding/json"
	"flag"
	"os"
	"path/filepath"

	"github.com/harbor/ldap-shadow-sync/internal/db"
	"github.com/harbor/ldap-shadow-sync/internal/model"
	"github.com/harbor/ldap-shadow-sync/internal/staging"
	"github.com/harbor/ldap-shadow-sync/merge"
)

type shadowDoc struct {
	Entries    []model.Entry `json:"entries"`
	EntryCount int           `json:"entry_count"`
}

type auditDoc struct {
	UniqueDNCount         int               `json:"unique_dn_count"`
	ChangelogLinesApplied int               `json:"changelog_lines_applied"`
	MaxUSN                int64             `json:"max_usn"`
	ExportSequence        int               `json:"export_sequence"`
	ReplayStats           model.IngestStats `json:"replay_stats"`
}

func Run(args []string) error {
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	dbPath := fs.String("db", "/app/state/shadow.db", "sqlite path")
	shadowOut := fs.String("shadow", "/app/output/shadow.json", "shadow json path")
	auditOut := fs.String("audit", "/app/output/shadow-audit.json", "audit json path")
	if err := fs.Parse(args); err != nil {
		return err
	}

	store, err := db.Open(*dbPath)
	if err != nil {
		return err
	}
	defer store.Close()

	entries, err := store.AllEntries()
	if err != nil {
		return err
	}
	staged, err := staging.ReadAll()
	if err != nil {
		return err
	}
	stats, err := staging.ReadIngestStats()
	if err != nil {
		return err
	}

	for i := range entries {
		for _, ch := range staged {
			if ch.NormalizedDN != entries[i].NormalizedDN {
				continue
			}
			if len(ch.ModifyOps) > 0 {
				entries[i].Attrs = merge.ApplyMods(entries[i].Attrs, ch.ModifyOps)
			}
		}
	}
	db.SortEntries(entries)

	lineCount, err := staging.LineCount()
	if err != nil {
		return err
	}
	maxUSN, err := store.MaxUSN()
	if err != nil {
		return err
	}
	seq, err := store.BumpExportSequence()
	if err != nil {
		return err
	}

	shadow := shadowDoc{
		Entries:    entries,
		EntryCount: lineCount,
	}
	if err := writeJSON(*shadowOut, shadow); err != nil {
		return err
	}

	audit := auditDoc{
		UniqueDNCount:         lineCount,
		ChangelogLinesApplied: lineCount,
		MaxUSN:                maxUSN,
		ExportSequence:        seq,
		ReplayStats:           stats,
	}
	return writeJSON(*auditOut, audit)
}

func writeJSON(path string, v any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0o644)
}
