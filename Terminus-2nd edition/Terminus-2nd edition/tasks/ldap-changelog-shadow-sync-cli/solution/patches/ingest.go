package ingest

import (
	"flag"
	"fmt"
	"sort"

	"github.com/harbor/ldap-shadow-sync/internal/db"
	"github.com/harbor/ldap-shadow-sync/internal/dn"
	"github.com/harbor/ldap-shadow-sync/internal/ldif"
	"github.com/harbor/ldap-shadow-sync/internal/model"
	"github.com/harbor/ldap-shadow-sync/internal/replay"
	"github.com/harbor/ldap-shadow-sync/internal/staging"
)

func Run(args []string) error {
	fs := flag.NewFlagSet("ingest-ldif", flag.ExitOnError)
	input := fs.String("input", "", "ldif changelog path")
	dbPath := fs.String("db", "/app/state/shadow.db", "sqlite path")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *input == "" {
		return fmt.Errorf("--input required")
	}
	records, err := ldif.ParseFile(*input)
	if err != nil {
		return err
	}
	sort.SliceStable(records, func(i, j int) bool {
		return records[i].ChangeNumber < records[j].ChangeNumber
	})
	store, err := db.Open(*dbPath)
	if err != nil {
		return err
	}
	defer store.Close()

	seen, err := store.AllUSNs()
	if err != nil {
		return err
	}
	shadow := map[string]model.Entry{}
	existing, err := store.AllEntries()
	if err != nil {
		return err
	}
	for _, e := range existing {
		shadow[e.NormalizedDN] = e
	}

	var newUSNs, replayNoop int
	for _, rec := range records {
		normDN := dn.NormalizeDN(rec.DN)
		if !replay.ShouldApply(rec.USNChanged, seen) {
			replayNoop++
			continue
		}
		newUSNs++
		ch := staging.ApplyRecord(shadow, rec, normDN)
		if err := staging.AppendChange(ch); err != nil {
			return err
		}
		switch rec.ChangeType {
		case "delete":
			if err := store.DeleteEntry(normDN); err != nil {
				return err
			}
		default:
			if err := store.UpsertEntry(shadow[normDN]); err != nil {
				return err
			}
		}
		if err := store.MarkUSN(rec.USNChanged); err != nil {
			return err
		}
		seen[rec.USNChanged] = struct{}{}
	}
	return staging.WriteIngestStats(model.IngestStats{
		NewUSNs:    newUSNs,
		ReplayNoop: replayNoop,
	})
}
