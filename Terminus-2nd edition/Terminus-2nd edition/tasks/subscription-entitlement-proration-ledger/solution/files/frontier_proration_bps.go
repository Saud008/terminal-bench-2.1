package prorateengine

import "github.com/terminus/subledctl/internal/cyclewindow"

type Plan struct {
    PlanID       string
    MonthlyCents int64
}

func SegmentBase(monthly int64, segStart, segEnd, cycleStart, cycleEnd string) (int64, int, error) {
    segDays, err := cyclewindow.InclusiveDays(segStart, segEnd)
    if err != nil {
        return 0, 0, err
    }
    cycleDays, err := cyclewindow.InclusiveDays(cycleStart, cycleEnd)
    if err != nil {
        return 0, 0, err
    }
    if cycleDays <= 0 {
        return 0, segDays, nil
    }
    return monthly * int64(segDays) / int64(cycleDays), segDays, nil
}

func ChangeCredit(oldMonthly int64, changeDate, cycleStart, cycleEnd string) (int64, error) {
    rem, err := cyclewindow.InclusiveDays(changeDate, cycleEnd)
    if err != nil {
        return 0, err
    }
    cycleDays, err := cyclewindow.InclusiveDays(cycleStart, cycleEnd)
    if err != nil || cycleDays <= 0 {
        return 0, err
    }
    return oldMonthly * int64(rem) / int64(cycleDays), nil
}
