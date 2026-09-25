package keyfold

import (
    "strings"
    "unicode/utf8"

    "golang.org/x/text/unicode/norm"
)

func Canonical(raw string) string {
    k := strings.TrimSpace(raw)
    k = norm.NFC.String(k)
    if strings.HasPrefix(k, "user:") {
        rest := strings.TrimPrefix(k, "user:")
        k = "user:" + strings.ToLower(rest)
    }
    return k
}

func ValidUTF8(s string) bool {
    return utf8.ValidString(s)
}

func FoldPrefix(raw string) string {
    k := strings.TrimSpace(raw)
    if strings.HasPrefix(k, "user:") {
        return "user:"
    }
    return ""
}

func NormalizeUserPrefix(raw string) string {
    k := strings.TrimSpace(raw)
    k = norm.NFC.String(k)
    if strings.HasPrefix(k, "user:") {
        rest := strings.TrimPrefix(k, "user:")
        return "user:" + strings.ToLower(rest)
    }
    return k
}
