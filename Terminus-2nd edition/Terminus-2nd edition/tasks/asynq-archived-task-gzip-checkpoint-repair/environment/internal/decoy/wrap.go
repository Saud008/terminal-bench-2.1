package decoy

import "github.com/terminus/asynq-archive-repair/internal/model"

// WrapTasks is a legacy compatibility helper kept off the archive hot path.
func WrapTasks(tasks []model.TaskRecord) []model.TaskRecord {
	out := make([]model.TaskRecord, len(tasks))
	copy(out, tasks)
	return out
}
