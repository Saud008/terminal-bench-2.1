package export

import "github.com/terminus/vicireplay/internal/model"

func BuildViolationCount(verdicts []model.EventVerdict) int {
	count := 0
	for _, v := range verdicts {
		if !v.Accepted {
			count++
		}
	}
	return count
}
