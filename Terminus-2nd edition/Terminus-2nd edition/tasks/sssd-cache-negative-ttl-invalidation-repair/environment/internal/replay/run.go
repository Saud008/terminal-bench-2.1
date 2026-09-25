package replay

import (
	"os"

	"github.com/terminus/sssdcache/internal/apperr"
	"github.com/terminus/sssdcache/internal/config"
	"github.com/terminus/sssdcache/internal/model"
	"github.com/terminus/sssdcache/internal/parse"
	"github.com/terminus/sssdcache/internal/staging"
	"github.com/terminus/sssdcache/internal/store"
)

func Run(opsDir, cfgPath, snapshotPath, dbPath string) (int, error) {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return apperr.ExitError, err
	}
	files, err := resolveOpFiles(opsDir)
	if err != nil {
		return apperr.ExitError, err
	}

	var ops []model.Op
	stats := model.Stats{}
	for _, file := range files {
		if err := parse.ReadLines(file, func(line string) error {
			stats.LinesRead++
			op, err := parse.ParseLine(line)
			if err != nil {
				stats.ParseErrors++
				return nil
			}
			ops = append(ops, op)
			return nil
		}); err != nil {
			return apperr.ExitError, err
		}
	}

	state, replayStats := Replay(ops, cfg)
	stats.LookupMiss = replayStats.LookupMiss
	stats.LookupHit = replayStats.LookupHit
	stats.CachePut = replayStats.CachePut
	stats.CacheDel = replayStats.CacheDel
	stats.NegativeCreated = replayStats.NegativeCreated
	stats.NegativeRefreshed = replayStats.NegativeRefreshed
	stats.GroupAddMember = replayStats.GroupAddMember
	stats.GroupInvalidations = replayStats.GroupInvalidations
	stats.ExplicitInvalidation = replayStats.ExplicitInvalidation
	stats.OpsApplied = replayStats.OpsApplied
	stats.ParseErrors += replayStats.ParseErrors

	snap := staging.Build(state, stats)
	ck, err := store.PersistSnapshot(dbPath, snap)
	if err != nil {
		return apperr.ExitError, err
	}
	stats.WALCheckpoints = ck
	snap.Stats.WALCheckpoints = ck
	if err := staging.Write(snapshotPath, state, stats); err != nil {
		return apperr.ExitError, err
	}
	return apperr.ExitOK, nil
}

func resolveOpFiles(path string) ([]string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}
	if !info.IsDir() {
		return []string{path}, nil
	}
	return parse.DiscoverJSONL(path)
}
