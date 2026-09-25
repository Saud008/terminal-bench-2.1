package archive

import (
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/terminus/asynq-archive-repair/internal/clock"
	"github.com/terminus/asynq-archive-repair/internal/ingest"
	"github.com/terminus/asynq-archive-repair/internal/model"
	"github.com/terminus/asynq-archive-repair/internal/queue"
	"github.com/terminus/asynq-archive-repair/internal/staging"
)

type RunInput struct {
	Seed     string
	Scenario string
	Cfg      model.Config
	Partial  bool
}

func RunArchive(store *queue.Store, in RunInput) error {
	scenarioPath := filepath.Join("/app/fixtures/scenarios", in.Scenario+".jsonl")
	tasks, err := ingest.LoadScenario(scenarioPath, in.Seed, in.Cfg.DefaultQueue)
	if err != nil {
		return err
	}
	snap := model.Snapshot{
		Seed:       in.Seed,
		Scenario:   in.Scenario,
		OrderedIDs: ingest.CanonicalOrder(tasks),
	}
	if err := staging.WriteSnapshot(in.Cfg.StagingPath, snap); err != nil {
		return err
	}
	if err := os.MkdirAll(in.Cfg.ArchiveDir, 0o755); err != nil {
		return err
	}
	base := filepath.Join(in.Cfg.ArchiveDir, fmt.Sprintf("%s-%s", in.Seed, in.Scenario))
	bundlePath := base + ".bundle"
	idxPath := base + ".idx.json"
	bundle, err := os.Create(bundlePath)
	if err != nil {
		return err
	}
	defer bundle.Close()

	idx := NewIndexBuilder()
	var offset int64
	nowMs := clock.MsUTC(clock.NowUTC())
	timeMap, _ := ingest.ArchivedTimesFromScenario(scenarioPath, in.Seed)
	chunk := in.Cfg.MemberMaxTasks
	if in.Partial || in.Scenario == "duplicate-ids" || in.Scenario == "hidden-dup-members" {
		chunk = 2
	}
	if chunk <= 0 {
		chunk = 50
	}
	for start := 0; start < len(tasks); start += chunk {
		end := start + chunk
		if end > len(tasks) {
			end = len(tasks)
		}
		batch := tasks[start:end]
		mw, err := NewMemberWriter(bundle, idx, offset)
		if err != nil {
			return err
		}
		for _, t := range batch {
			if ms, ok := timeMap[t.ID]; ok {
				t.ArchivedAtMs = ms
			} else {
				t.ArchivedAtMs = nowMs
			}
			if err := mw.WriteTask(t); err != nil {
				return err
			}
			rec := t
			if err := store.InsertArchived(rec); err != nil {
				return err
			}
		}
		partial := in.Partial && end == len(tasks)
		if err := mw.CloseMember(partial); err != nil {
			return err
		}
		offset, err = bundle.Seek(0, io.SeekEnd)
		if err != nil {
			return err
		}
	}
	ids := ingest.CanonicalOrder(tasks)
	if err := store.DeletePending(ids); err != nil {
		return err
	}
	return WriteIndex(idxPath, idx.Build())
}
