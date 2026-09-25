package x509norm

import "strings"

func NormalizeSerial(raw string) string {
    s := strings.TrimSpace(raw)
    return strings.ToUpper(s)
}
