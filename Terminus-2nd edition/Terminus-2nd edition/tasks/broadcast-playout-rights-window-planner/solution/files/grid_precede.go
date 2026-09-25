package darkregion

import (
    "time"

    "github.com/terminus/gridplan/internal/model"
)

func Blocked(region, startUTC string, blackouts []model.Blackout, _ bool) bool {
    air, err := time.Parse(time.RFC3339, startUTC)
    if err != nil {
        return false
    }
    best := -1
    hit := false
    for _, b := range blackouts {
        if b.Region != region {
            continue
        }
        start, err1 := time.Parse(time.RFC3339, b.StartUTC)
        end, err2 := time.Parse(time.RFC3339, b.EndUTC)
        if err1 != nil || err2 != nil {
            continue
        }
        if !air.Before(start) && air.Before(end) {
            if b.Precedence > best {
                best = b.Precedence
                hit = true
            }
        }
    }
    return hit
}
