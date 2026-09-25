package rrule

import (
	"time"

	"github.com/terminus/icalexpand/internal/model"
)

func withinUntil(candidate time.Time, rule model.RRule, dtStart time.Time) bool {
	if rule.Until == nil {
		return true
	}
	until := *rule.Until
	if !rule.UntilUTC {
		return candidate.Before(until)
	}
	return !candidate.After(until)
}
