package restore

import (
	"github.com/terminus/asynq-archive-repair/internal/archive"
	"github.com/terminus/asynq-archive-repair/internal/model"
	"github.com/terminus/asynq-archive-repair/internal/queue"
)

func ImportBundle(store *queue.Store, bundlePath string, idx model.IndexFile) error {
	final := map[string]model.TaskRecord{}
	for _, member := range idx.Members {
		tasks, err := archive.ReadMemberTasks(bundlePath, member)
		if err != nil {
			return err
		}
		for _, t := range tasks {
			final[t.ID] = t
		}
	}
	for _, t := range final {
		if err := store.InsertPending(t); err != nil {
			return err
		}
	}
	return nil
}
