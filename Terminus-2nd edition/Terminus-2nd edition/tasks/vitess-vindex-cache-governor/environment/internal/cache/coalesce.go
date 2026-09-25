package cache

import "vtgatesim/internal/model"

func DropForeignGeneration(entries []model.CacheEntry, generation int) (kept []model.CacheEntry, dropped int) {
	for _, e := range entries {
		if e.Generation == generation {
			kept = append(kept, e)
		} else {
			dropped++
		}
	}
	return kept, dropped
}
