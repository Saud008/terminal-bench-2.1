package formndc

import (
    "fmt"
    "strings"
)

func NormalizeNDC(raw string) string {
    digits := strings.ReplaceAll(raw, "-", "")
    digits = fmt.Sprintf("%011s", digits)
    digits = strings.ReplaceAll(digits, " ", "0")
    return digits[:5] + "-" + digits[5:9] + "-" + digits[9:11]
}
