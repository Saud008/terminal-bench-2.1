package ttl

type Tracker struct {
	expires map[string]int
	ttlMS   int
}

func NewTracker(ttlMS int) *Tracker {
	return &Tracker{
		expires: map[string]int{},
		ttlMS:   ttlMS,
	}
}

func (t *Tracker) OnStart(respondent string, nowMS int) {
	t.expires[respondent] = nowMS + t.ttlMS
}

func (t *Tracker) OnReconnect(respondent string, nowMS int) {
	t.expires[respondent] = nowMS + t.ttlMS
}

func (t *Tracker) ExpiresMS(respondent string) int {
	return t.expires[respondent]
}

func (t *Tracker) Active(respondent string, nowMS int) bool {
	exp, ok := t.expires[respondent]
	if !ok {
		return false
	}
	return nowMS <= exp
}
