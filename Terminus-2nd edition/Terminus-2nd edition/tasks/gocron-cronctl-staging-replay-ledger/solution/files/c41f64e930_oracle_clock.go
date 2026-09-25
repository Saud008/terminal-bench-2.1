package clock

import (
	"os"
	"strconv"
	"time"
)

type Fake struct {
	Now time.Time
}

// FromEnv returns a controllable clock. TB3_CLOCK_START (RFC3339) overrides
// the default window start when set to a valid timestamp.
func FromEnv(defaultStart time.Time) Fake {
	start := defaultStart
	if raw := os.Getenv("TB3_CLOCK_START"); raw != "" {
		if t, err := time.Parse(time.RFC3339, raw); err == nil {
			start = t
		}
	}
	return Fake{Now: start}
}

// TickMs returns TB3_TICK_MS when set to a positive integer, otherwise cfgDefault.
func TickMs(cfgDefault int64) int64 {
	if raw := os.Getenv("TB3_TICK_MS"); raw != "" {
		if v, err := strconv.ParseInt(raw, 10, 64); err == nil && v > 0 {
			return v
		}
	}
	return cfgDefault
}

func (f *Fake) Advance(ms int64) {
	f.Now = f.Now.Add(time.Duration(ms) * time.Millisecond)
}
