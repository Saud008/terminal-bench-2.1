package lock

import "github.com/terminus/gocron-overlap-repair/internal/model"

type SingletonGuard struct {
	active map[string]struct{}
}

func NewSingletonGuard() *SingletonGuard {
	return &SingletonGuard{active: map[string]struct{}{}}
}

func groupKey(job model.JobSpec) string {
	if g, ok := job.Tags["singleton_group"]; ok && g != "" {
		return "group:" + g
	}
	return "job:" + job.ID
}

func (g *SingletonGuard) TryEnter(job model.JobSpec) bool {
	if !job.Singleton && job.Tags["singleton_group"] == "" {
		return true
	}
	key := groupKey(job)
	if _, ok := g.active[key]; ok {
		return false
	}
	g.active[key] = struct{}{}
	return true
}

func (g *SingletonGuard) Exit(job model.JobSpec) {
	key := groupKey(job)
	delete(g.active, key)
}
