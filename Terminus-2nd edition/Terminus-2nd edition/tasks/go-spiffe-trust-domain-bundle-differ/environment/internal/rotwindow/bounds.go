package rotwindow

import (
    "os"
    "strconv"
)

const DefaultWindow = 5

func WindowSize() int {
    if raw := os.Getenv("TB3_ROT_WINDOW"); raw != "" {
        if v, err := strconv.Atoi(raw); err == nil && v > 0 {
            return v
        }
    }
    return DefaultWindow
}

func InWindow(epoch, bundleEpoch int) bool {
    win := WindowSize()
    min := bundleEpoch - win
    max := bundleEpoch
    return epoch > min && epoch < max
}
