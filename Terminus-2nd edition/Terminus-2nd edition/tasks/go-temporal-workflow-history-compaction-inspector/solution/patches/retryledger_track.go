package retryledger

type Tracker struct {
    attempts map[string]int
}

func NewTracker() *Tracker {
    return &Tracker{attempts: map[string]int{}}
}

func (t *Tracker) OnScheduled(activityID string, attempt int) int {
    if attempt > 0 {
        t.attempts[activityID] = attempt
        return attempt
    }
    t.attempts[activityID] = t.attempts[activityID] + 1
    return t.attempts[activityID]
}

func (t *Tracker) OnContinuedAsNew() {
    t.attempts = map[string]int{}
}

func (t *Tracker) MaxAttempt(activityID string) int {
    return t.attempts[activityID]
}
