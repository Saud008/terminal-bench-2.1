package anchorsync

import "time"

type Shift struct {
    EffectiveDate string
    NewAnchorDay  int
}

func AdjustWindowEnd(windowStart, windowEnd, cycleEnd string, shifts []Shift) string {
	we, _ := time.Parse("2006-01-02", windowEnd)
	ce, _ := time.Parse("2006-01-02", cycleEnd)
	end := we
    for _, sh := range shifts {
        eff, err := time.Parse("2006-01-02", sh.EffectiveDate)
        if err != nil || eff.After(we) {
            continue
        }
        y, m, _ := eff.Date()
        day := sh.NewAnchorDay
        if day > 28 {
            day = 28
        }
        candidate := time.Date(y, m, day, 0, 0, 0, 0, time.UTC)
        for candidate.Before(eff) {
            candidate = candidate.AddDate(0, 1, 0)
        }
        if !candidate.After(end) && !candidate.After(ce) {
            end = candidate
        }
    }
    return end.Format("2006-01-02")
}
