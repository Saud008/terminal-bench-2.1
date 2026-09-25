package deletefile

import (
    "os"
    "strconv"
)

const DefaultRetentionHours int64 = 168

func RetentionHours(envDefault int64) int64 {
    if raw := os.Getenv("TB3_DELETE_RETENTION_HOURS"); raw != "" {
        if v, err := strconv.ParseInt(raw, 10, 64); err == nil && v > 0 {
            return v
        }
    }
    if envDefault > 0 {
        return envDefault
    }
    return DefaultRetentionHours
}

func DeleteEligible(eventMs, currentTs, retentionHours int64) bool {
    floor := currentTs - retentionHours*3600*1000
    return eventMs >= floor
}
