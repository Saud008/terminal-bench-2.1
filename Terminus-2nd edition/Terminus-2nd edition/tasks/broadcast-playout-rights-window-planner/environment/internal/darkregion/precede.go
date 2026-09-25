package darkregion

import (
    "strings"
    "time"

    "github.com/terminus/gridplan/internal/model"
)

func Blocked(region, startUTC string, blackouts []model.Blackout, rightsAlreadyOK bool) bool {
    if !rightsAlreadyOK {
        return false
    }
    air, err := time.Parse(time.RFC3339, startUTC)
    if err != nil {
        return false
    }
    best := -1
    var hit *model.Blackout
    for i := range blackouts {
        b := blackouts[i]
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
                hit = &blackouts[i]
            }
        }
    }
    return hit != nil && strings.HasPrefix(hit.BlackoutID, "B")
}
