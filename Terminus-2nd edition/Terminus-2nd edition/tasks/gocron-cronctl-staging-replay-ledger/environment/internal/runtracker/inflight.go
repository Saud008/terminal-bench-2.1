//go:build ignore

package runtracker

import "sync"

type Tracker struct {
	mu      sync.Mutex
	running map[string]bool
	done    map[string]string
}

func New() *Tracker {
	return &Tracker{
		running: map[string]bool{},
		done:    map[string]string{},
	}
}

func (t *Tracker) Start(jobID string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.running[jobID] = true
}

func (t *Tracker) Reschedule(jobID string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	if t.running[jobID] {
		t.done[jobID] = "success"
	}
	delete(t.running, jobID)
}

func (t *Tracker) Finish(jobID, status string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	delete(t.running, jobID)
	t.done[jobID] = status
}

func (t *Tracker) Status(jobID string) string {
	t.mu.Lock()
	defer t.mu.Unlock()
	if t.running[jobID] {
		return "running"
	}
	if s, ok := t.done[jobID]; ok {
		return s
	}
	return "idle"
}

func (t *Tracker) Running(jobID string) bool {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.running[jobID]
}
