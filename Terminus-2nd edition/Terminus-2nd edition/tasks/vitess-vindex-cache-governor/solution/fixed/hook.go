package migration

import (
	"encoding/json"
	"os"

	"vtgatesim/internal/cache"
	"vtgatesim/internal/model"
)

func ApplyEvent(store *cache.Store, snap *model.Snapshot, ev model.MigrationEvent) error {
	switch ev.Op {
	case "load_shard_map":
		data, err := os.ReadFile(ev.ShardMap)
		if err != nil {
			return err
		}
		var sm model.ShardMap
		if err := json.Unmarshal(data, &sm); err != nil {
			return err
		}
		snap.Generation = sm.Generation
		snap.ShardMapPath = ev.ShardMap
		snap.MigrationID = ev.Migration
	case "rollback":
		data, err := os.ReadFile(ev.ShardMap)
		if err != nil {
			return err
		}
		var sm model.ShardMap
		if err := json.Unmarshal(data, &sm); err != nil {
			return err
		}
		store.Flush()
		snap.Generation = sm.Generation
		snap.ShardMapPath = ev.ShardMap
		snap.MigrationID = ev.Migration
		snap.Cache = []model.CacheEntry{}
	default:
		return nil
	}
	return nil
}
