package ingest

import (
	"path/filepath"

	"github.com/clickparts/chparts/internal/commit"
	"github.com/clickparts/chparts/internal/config"
	"github.com/clickparts/chparts/internal/merge"
	"github.com/clickparts/chparts/internal/model"
	"github.com/clickparts/chparts/internal/staging"
	"github.com/clickparts/chparts/internal/store"
	"github.com/clickparts/chparts/internal/ttl"
)

func Run(partsDir, cfgPath, dbPath string) error {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return err
	}
	tableName := config.TableName()
	st, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer st.Close()
	if err := st.EnsureTable(tableName); err != nil {
		return err
	}

	emptySnap := model.Snapshot{TableSuffix: config.TableSuffix(), TableName: tableName}
	if err := staging.WriteEarlyManifest(emptySnap); err != nil {
		return err
	}

	dirs, err := ListPartDirs(partsDir)
	if err != nil {
		return err
	}

	var allRows []model.Row
	var maxBlock int64
	ingested := 0

	for _, dir := range dirs {
		meta, rows, err := LoadPartDir(dir)
		if err != nil {
			return err
		}
		key := IngestKey(meta.BatchID, meta.PartID)
		skip, err := ShouldSkipReplay(st, key)
		if err != nil {
			return err
		}
		if skip {
			continue
		}
		ingested++

		if err := RegisterPart(st, meta); err != nil {
			return err
		}

		dataPath := filepath.Join(dir, "data.tsv")
		sum, err := ChecksumFile(dataPath)
		if err != nil {
			return err
		}
		ok := sum == meta.Checksum
		if err := ApplyChecksum(st, meta.PartID, ok); err != nil {
			return err
		}
		if !ok {
			return checksumFail(meta.PartID)
		}

		if err := ttl.DropExpired(st, tableName, cfg.TTLGraceMS); err != nil {
			return err
		}

		if err := st.InsertRows(tableName, rows); err != nil {
			return err
		}
		allRows = append(allRows, rows...)
		if meta.MaxBlock > maxBlock {
			maxBlock = meta.MaxBlock
		}
		if err := RecordReplay(st, key, meta.PartID); err != nil {
			return err
		}
	}

	var merged []model.MergedRow
	var snapMax int64
	var fsynced bool
	rowsForStats := allRows

	if ingested == 0 && len(dirs) > 0 {
		stored, err := st.ListRows(tableName)
		if err != nil {
			return err
		}
		rowsForStats = stored
		merged = merge.MergeRows(stored)
		merged = ttl.PruneMerged(merged, cfg.TTLGraceMS)
		maxBlock, fsynced, err = st.CommitState()
		if err != nil {
			return err
		}
	} else {
		merged = merge.MergeRows(allRows)
		merged = ttl.PruneMerged(merged, cfg.TTLGraceMS)
		if err := commit.FinalizeCommit(st, maxBlock); err != nil {
			return err
		}
		maxBlock, fsynced, err = st.CommitState()
		if err != nil {
			return err
		}
	}

	if fsynced {
		snapMax = maxBlock
	}

	stats, err := st.PartStats()
	if err != nil {
		return err
	}
	for i := range stats {
		for _, r := range rowsForStats {
			if r.PartID == stats[i].PartID {
				stats[i].RowCount++
			}
		}
	}

	snap := model.Snapshot{
		TableSuffix: config.TableSuffix(),
		TableName:   tableName,
		MaxBlock:    snapMax,
		Fsynced:     fsynced,
		Parts:       stats,
		Rows:        merged,
	}
	if err := staging.WriteSnapshot(snap); err != nil {
		return err
	}
	return nil
}
