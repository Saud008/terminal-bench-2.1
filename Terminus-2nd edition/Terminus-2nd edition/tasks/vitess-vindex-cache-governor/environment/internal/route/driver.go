package route

import (
	"encoding/json"
	"os"

	"vtgatesim/internal/cache"
	"vtgatesim/internal/model"
	"vtgatesim/internal/planner"
	"vtgatesim/internal/staging"
)

func Run(snapshotPath, batchPath string) (model.RoutePlan, error) {
	snap, err := staging.ReadSnapshot(snapshotPath)
	if err != nil {
		return model.RoutePlan{}, err
	}
	sm, err := loadShardMap(snap.ShardMapPath)
	if err != nil {
		return model.RoutePlan{}, err
	}
	batchData, err := os.ReadFile(batchPath)
	if err != nil {
		return model.RoutePlan{}, err
	}
	var batch model.RouteBatch
	if err := json.Unmarshal(batchData, &batch); err != nil {
		return model.RoutePlan{}, err
	}
	catalog := map[string]model.VindexDef{}
	for _, v := range snap.Vindexes {
		catalog[v.Name] = v
	}
	store := cache.NewStore(snap.Cache)
	plan := model.RoutePlan{Generation: sm.Generation, ScatterOK: true, Routes: []model.RouteResult{}}
	for _, q := range batch.Queries {
		res, hit, err := planner.RouteQuery(sm, catalog, store, q)
		if err != nil {
			plan.ScatterOK = false
			continue
		}
		if hit {
			plan.CacheHits++
		}
		plan.Routes = append(plan.Routes, res)
	}
	return plan, nil
}

func loadShardMap(path string) (model.ShardMap, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.ShardMap{}, err
	}
	var sm model.ShardMap
	if err := json.Unmarshal(data, &sm); err != nil {
		return model.ShardMap{}, err
	}
	return sm, nil
}
