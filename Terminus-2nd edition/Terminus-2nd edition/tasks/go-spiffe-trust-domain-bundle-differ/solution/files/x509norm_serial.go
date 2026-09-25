package x509norm

import "strings"

func NormalizeSerial(raw string) string {
    s := strings.ToLower(strings.TrimSpace(raw))
    s = strings.TrimLeft(s, "0")
    if s == "" {
        return "0"
    }
    return s
}
