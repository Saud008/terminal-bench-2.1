package cyclewindow

import "time"

func InclusiveDays(start, end string) (int, error) {
    a, err := time.Parse("2006-01-02", start)
    if err != nil {
        return 0, err
    }
    b, err := time.Parse("2006-01-02", end)
    if err != nil {
        return 0, err
    }
    if b.Before(a) {
        return 0, nil
    }
    return int(b.Sub(a).Hours()/24) + 1, nil
}
