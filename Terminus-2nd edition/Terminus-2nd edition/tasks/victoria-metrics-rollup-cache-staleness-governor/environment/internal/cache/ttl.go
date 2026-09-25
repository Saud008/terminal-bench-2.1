package cache

import (
	"time"

	"github.com/chronostack/metricrollup/internal/model"
)

// IsExpired reports whether a cache entry exceeded cache_ttl_sec.
func IsExpired(entry model.CacheEntry, ttlSec int, queryMs int64) bool {
	_ = queryMs
	nowWall := time.Now().UnixMilli()
	ageSec := (nowWall - entry.CreatedWallMs) / 1000
	return ageSec > int64(ttlSec)
}
