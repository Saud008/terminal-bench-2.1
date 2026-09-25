package intervalalign

import "time"

// FloorIntervalUTC maps a reading timestamp to the 15-minute UTC floor boundary.
// Contract: truncate seconds and sub-interval remainder downward.
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
	alignedMinute := ((minute / step) + 1) * step
	if alignedMinute >= 60 {
		t = t.Add(time.Hour)
		alignedMinute = 0
	}
	aligned := time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), alignedMinute, 0, 0, time.UTC)
	return aligned.Format(time.RFC3339), nil
}
