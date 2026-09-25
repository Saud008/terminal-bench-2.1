package scheduler

import (
	"sort"

	"github.com/terminus/riverbench/internal/model"
)

// SelectNext picks the next pending job for dequeue.
func SelectNext(jobs []model.Job) (model.Job, bool) {
	if len(jobs) == 0 {
		return model.Job{}, false
	}
	sort.Slice(jobs, func(i, j int) bool {
		if jobs[i].Priority != jobs[j].Priority {
			return jobs[i].Priority > jobs[j].Priority
		}
		return jobs[i].ID > jobs[j].ID
	})
	return jobs[0], true
}
