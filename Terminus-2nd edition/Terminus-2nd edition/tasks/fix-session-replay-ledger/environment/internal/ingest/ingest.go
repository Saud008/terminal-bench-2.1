package ingest

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/harbor/fix-session-replay-ledger/internal/db"
	"github.com/harbor/fix-session-replay-ledger/internal/fixparse"
	"github.com/harbor/fix-session-replay-ledger/internal/model"
	"github.com/harbor/fix-session-replay-ledger/internal/staging"
)

func Run(sessionDir, dbPath string) error {
	store, err := db.Open(dbPath)
	if err != nil {
		return err
	}
	defer store.Close()

	entries, err := os.ReadDir(sessionDir)
	if err != nil {
		return err
	}
	var files []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		if strings.HasSuffix(e.Name(), ".fix") {
			files = append(files, e.Name())
		}
	}
	sort.Strings(files)

	var discovered []model.Execution
	inserted := 0
	for _, name := range files {
		path := filepath.Join(sessionDir, name)
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		rows, err := fixparse.ScanSessionFile(name, data)
		if err != nil {
			return err
		}
		for _, ex := range rows {
			discovered = append(discovered, ex)
			ok, err := store.InsertExecution(ex)
			if err != nil {
				return err
			}
			if ok {
				inserted++
			}
		}
	}

	all, err := store.AllExecutions()
	if err != nil {
		return err
	}
	if err := staging.WriteSnapshot(discovered, all); err != nil {
		return err
	}
	fmt.Printf("ingested=%d\n", inserted)
	return nil
}
