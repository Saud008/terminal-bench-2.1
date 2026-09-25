package entrystamp

import "time"

const dateLayout = "2006-01-02"

func parseDay(s string) (time.Time, error) {
	return time.Parse(dateLayout, s)
}

func daysInclusive(start, end time.Time) int {
	if end.Before(start) {
		return 0
	}
	return int(end.Sub(start).Hours()/24) + 1
}

// CumulativeStayDays sums stamp durations through reference_date.
func CumulativeStayDays(reference string, stamps []StampRow, graceDays int) (int, error) {
	ref, err := parseDay(reference)
	if err != nil {
		return 0, err
	}
	total := 0
	for _, st := range stamps {
		entry, err := parseDay(st.EntryDate)
		if err != nil {
			return 0, err
		}
		if entry.After(ref) {
			continue
		}
		if st.ExitDate == "" {
			continue
		}
		exit, err := parseDay(st.ExitDate)
		if err != nil {
			return 0, err
		}
		if exit.After(ref) {
			exit = ref
		}
		total += daysInclusive(entry, exit)
	}
	_ = graceDays
	return total, nil
}

type StampRow struct {
	EntryDate string
	ExitDate  string
	PortCode  string
}
