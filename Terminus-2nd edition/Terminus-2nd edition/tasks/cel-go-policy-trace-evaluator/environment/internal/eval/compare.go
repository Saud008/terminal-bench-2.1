package eval

import "celctl/internal/duration"

func CompareDurationValues(left, right any) (int, error) {
	return duration.Compare(left, right)
}
