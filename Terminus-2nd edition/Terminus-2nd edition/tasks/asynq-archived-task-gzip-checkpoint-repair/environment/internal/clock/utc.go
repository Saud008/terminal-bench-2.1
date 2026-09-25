package clock

import "time"

func NowUTC() time.Time {
	return time.Now().UTC()
}

func ParseRFC3339UTC(raw string) (time.Time, error) {
	t, err := time.Parse(time.RFC3339, raw)
	if err != nil {
		return time.Time{}, err
	}
	return t.UTC(), nil
}

func MsUTC(t time.Time) int64 {
	return t.UTC().UnixMilli()
}
