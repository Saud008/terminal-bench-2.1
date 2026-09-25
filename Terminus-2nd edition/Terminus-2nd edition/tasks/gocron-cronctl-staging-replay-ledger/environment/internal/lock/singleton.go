package lock

import "github.com/terminus/gocron-overlap-repair/internal/scheduler"

// SingletonGuard prevents duplicate concurrent runs.
type SingletonGuard struct {
	active map[string]struct{}
}

func NewSingletonGuard() *SingletonGuard {
	return &SingletonGuard{active: map[string]struct{}{}}
}

func (g *SingletonGuard) TryEnter(job scheduler.JobLike) bool {
	key := scheduler.OverlapKeyView(job.Spec())
	if _, ok := g.active[key]; ok {
		return false
	}
	g.active[key] = struct{}{}
	return true
}

func (g *SingletonGuard) Exit(job scheduler.JobLike) {
	delete(g.active, scheduler.OverlapKeyView(job.Spec()))
}

type jobWrap struct {
	spec scheduler.JobSpecView
}

func (j jobWrap) Spec() scheduler.JobSpecView { return j.spec }

func WrapJob(id, cron string) scheduler.JobLike {
	return jobWrap{spec: scheduler.JobSpecView{ID: id, Cron: cron}}
}
