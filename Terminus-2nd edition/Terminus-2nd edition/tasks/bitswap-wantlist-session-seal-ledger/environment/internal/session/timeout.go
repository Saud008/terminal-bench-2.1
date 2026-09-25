package session

import "wantplay/internal/model"

const DefaultIdleMS = 5000

func New(name string) *model.Session {
	return &model.Session{
		Name:        name,
		Wants:       map[string]*model.WantEntry{},
		InFlight:    map[string]*model.InFlight{},
		Partial:     map[string]*model.PartialBlock{},
		Ledger:      map[string]map[string]int{},
		Canceled:    map[string]bool{},
		Delivered:   []model.Delivery{},
		IdleLimitMS: DefaultIdleMS,
	}
}

// ApplyIdleTick advances idle clock and applies session idle cleanup.
func ApplyIdleTick(sess *model.Session, idleMS int) {
	sess.LastActivity += idleMS
	if sess.LastActivity >= sess.IdleLimitMS {
		sess.Wants = map[string]*model.WantEntry{}
	}
}

func Touch(sess *model.Session) {
	sess.LastActivity = 0
}
