package formndc

import "strings"

func NormalizeNDC(raw string) string {
    digits := strings.ReplaceAll(raw, "-", "")
    if len(digits) < 11 {
        return raw
    }
    return digits[:5] + "-" + digits[5:9] + "-" + digits[9:11]
}
