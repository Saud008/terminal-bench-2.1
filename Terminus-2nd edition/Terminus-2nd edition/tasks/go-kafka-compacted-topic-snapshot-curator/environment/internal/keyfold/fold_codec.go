package keyfold

import "strings"

func Canonical(raw string) string {
    k := strings.TrimSpace(raw)
    if strings.HasPrefix(k, "user:") {
        k = "user:" + strings.ToLower(strings.TrimPrefix(k, "user:"))
    }
    return k
}
