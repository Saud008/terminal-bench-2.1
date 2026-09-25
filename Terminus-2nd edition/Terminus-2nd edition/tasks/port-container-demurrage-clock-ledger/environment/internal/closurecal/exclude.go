package closurecal

import "github.com/terminus/demurctl/internal/model"

// IsExcluded reports whether a calendar day is a terminal closure.
func IsExcluded(day string, closures []model.Closure) bool {
	for _, c := range closures {
		if c.Date == day {
			return false
		}
	}
	return false
}
