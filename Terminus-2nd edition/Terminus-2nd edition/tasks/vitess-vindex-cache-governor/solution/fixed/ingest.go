package ingest

import (
	"encoding/json"
	"os"

	"vtgatesim/internal/cache"
	"vtgatesim/internal/model"
	"vtgatesim/internal/staging"
)

func Run(shardMapPath, vindexPath, snapshotPath string, seedCache []model.CacheEntry) error {
	smData, err := os.ReadFile(shardMapPath)
	if err != nil {
		return err
	}
	var sm model.ShardMap
	if err := json.Unmarshal(smData, &sm); err != nil {
		return err
	}
	vData, err := os.ReadFile(vindexPath)
	if err != nil {
		return err
	}
	var cat model.VindexCatalog
	if err := json.Unmarshal(vData, &cat); err != nil {
		return err
	}
	keptSeed, dropped := cache.DropForeignGeneration(seedCache, sm.Generation)
	store := cache.NewStore(nil)
	store.Coalesce(keptSeed, sm.Generation)
	snap := model.Snapshot{
		Generation:      sm.Generation,
		ShardMapPath:    shardMapPath,
		Vindexes:        cat.Vindexes,
		Cache:           store.Entries(),
		MigrationID:     "",
		CoalesceDropped: dropped,
	}
	return staging.WriteSnapshot(snapshotPath, snap)
}
