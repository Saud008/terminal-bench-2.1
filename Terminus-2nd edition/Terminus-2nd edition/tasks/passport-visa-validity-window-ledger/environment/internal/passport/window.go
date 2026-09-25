package passport

import "time"

const dateLayout = "2006-01-02"

func parseDay(s string) (time.Time, error) {
	return time.Parse(dateLayout, s)
}

// PassportValidAt reports whether reference falls inside the passport validity window.
func PassportValidAt(reference, issue, expiry string) (bool, error) {
	ref, err := parseDay(reference)
	if err != nil {
		return false, err
	}
	iss, err := parseDay(issue)
	if err != nil {
		return false, err
	}
	exp, err := parseDay(expiry)
	if err != nil {
		return false, err
	}
	if ref.Before(iss) {
		return false, nil
	}
	if !ref.Before(exp) {
		return false, nil
	}
	return true, nil
}
