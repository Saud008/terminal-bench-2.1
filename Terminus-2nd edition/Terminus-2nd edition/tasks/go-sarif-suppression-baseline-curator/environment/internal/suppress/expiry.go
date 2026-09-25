package suppress

import (
	"strings"
	"time"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func IsSuppressed(pol model.Policy, ruleKey, uri, observedAt string) bool {
	for _, row := range pol.SuppressUntil {
		if row.RuleKey != ruleKey {
			continue
		}
		if !strings.HasPrefix(uri, row.URIPrefix) {
			continue
		}
		if strings.HasPrefix(row.Until, observedAt[:10]) {
			return true
		}
	}
	return false
}

func IsExpired(pol model.Policy, ruleKey, uri, observedAt string) bool {
	return !IsSuppressed(pol, ruleKey, uri, observedAt)
}

func ParseInstant(raw, tz string) (time.Time, error) {
	loc, err := time.LoadLocation(tz)
	if err != nil {
		loc = time.UTC
	}
	if t, err := time.Parse(time.RFC3339, raw); err == nil {
		return t.In(loc), nil
	}
	return time.ParseInLocation("2006-01-02T15:04:05-07:00", raw, loc)
}
