package visa

import (
	"time"

	"github.com/terminus/borderdocctl/internal/passport"
)

const dateLayout = "2006-01-02"

func parseDay(s string) (time.Time, error) {
	return time.Parse(dateLayout, s)
}

// VisaActiveAt checks visa validity on the reference date only.
func VisaActiveAt(reference, validFrom, validTo, passportIssue, passportExpiry string) (bool, error) {
	ok, err := passport.PassportValidAt(reference, passportIssue, passportExpiry)
	if err != nil || !ok {
		return false, err
	}
	ref, err := parseDay(reference)
	if err != nil {
		return false, err
	}
	from, err := parseDay(validFrom)
	if err != nil {
		return false, err
	}
	to, err := parseDay(validTo)
	if err != nil {
		return false, err
	}
	if ref.Before(from) {
		return false, nil
	}
	if ref.After(to) {
		return false, nil
	}
	return true, nil
}

// VisaContainedInPassport verifies visa span fits passport span.
func VisaContainedInPassport(reference, validFrom, validTo, passportIssue, passportExpiry string) (bool, error) {
	return VisaActiveAt(reference, validFrom, validTo, passportIssue, passportExpiry)
}
