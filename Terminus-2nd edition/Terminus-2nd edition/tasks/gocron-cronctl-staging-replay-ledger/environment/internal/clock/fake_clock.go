//go:build ignore

package clock

import (
	"os"
	"strconv"
	"time"
)

type Fake struct {
	Now time.Time
}

func FromEnv(defaultStart time.Time) Fake {
	start := defaultStart
	if raw := os.Getenv("TB3_CLOCK_START"); raw != "" {
		if t, err := time.Parse(time.RFC3339, raw); err == nil {
			start = t
		}
	}
	return Fake{Now: start}
}

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
