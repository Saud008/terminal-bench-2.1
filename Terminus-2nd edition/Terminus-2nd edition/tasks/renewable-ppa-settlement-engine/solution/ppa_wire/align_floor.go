package intervalalign

import "time"

func FloorIntervalUTC(ts string, intervalMinutes int) (string, error) {
	t, err := time.Parse(time.RFC3339, ts)
	if err != nil {
		return "", err
	}
	t = t.UTC()
	step := intervalMinutes
	if step <= 0 {
		step = 15
	}
	minute := t.Minute()
	alignedMinute := (minute / step) * step
	aligned := time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), alignedMinute, 0, 0, time.UTC)
	return aligned.Format(time.RFC3339), nil
}
