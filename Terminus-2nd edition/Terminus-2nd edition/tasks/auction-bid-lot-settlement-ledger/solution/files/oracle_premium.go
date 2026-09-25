package buyerfee

import (
    "encoding/json"
    "os"
    "strconv"

    "github.com/terminus/auctctl/internal/store"
)

func BuyerPremiumCents(hammer int64, tier string) (int64, error) {
    db, err := store.Open()
    if err != nil {
        return 0, err
    }
    defer db.Close()
    raw, err := store.GetMeta(db, "premium_schedule")
    if err != nil {
        return 0, err
    }
    var sched map[string]struct {
        RateBPS  int64 `json:"rate_bps"`
        CapCents int64 `json:"cap_cents"`
    }
    if err := json.Unmarshal([]byte(raw), &sched); err != nil {
        return 0, err
    }
    row, ok := sched[tier]
    if !ok {
        row = sched["standard"]
    }
    rate := row.RateBPS
    if env := os.Getenv("TB3_PREMIUM_BPS"); env != "" {
        if v, err := strconv.ParseInt(env, 10, 64); err == nil {
            rate = v
        }
    }
    prem := hammer * rate / 10000
    if prem > row.CapCents {
        prem = row.CapCents
    }
    return prem, nil
}
