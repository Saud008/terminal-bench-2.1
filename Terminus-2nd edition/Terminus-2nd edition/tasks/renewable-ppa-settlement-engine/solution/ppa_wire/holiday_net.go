package holidayrollup

import (
	"time"

	"github.com/terminus/ppareconctl/internal/model"
)

func BillingDays(sc *model.Scenario) (int, error) {
	start, err := time.Parse("2006-01-02", sc.PeriodStart)
	if err != nil {
		return 0, err
	}
	end, err := time.Parse("2006-01-02", sc.PeriodEnd)
	if err != nil {
		return 0, err
	}
	holidaySet := map[string]struct{}{}
	for _, h := range sc.Holidays {
		holidaySet[h] = struct{}{}
	}
	days := 0
	trim := 0
	for d := start; !d.After(end); d = d.AddDate(0, 0, 1) {
		days++
		key := d.Format("2006-01-02")
		if _, ok := holidaySet[key]; ok {
			trim++
		}
	}
	return days - trim, nil
}
