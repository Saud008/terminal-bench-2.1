package exhibitlink

import (
    "regexp"
    "strings"
)

var baseExhibitRe = regexp.MustCompile(`(?i)Exhibit\s+(\d+)`)

// ParseExhibitRefs extracts exhibit labels from filing line text.
func ParseExhibitRefs(text string) []string {
    var out []string
    for _, m := range baseExhibitRe.FindAllStringSubmatch(text, -1) {
        if len(m) > 1 {
            out = append(out, "Exhibit "+m[1])
        }
    }
    return dedupe(out)
}

func dedupe(items []string) []string {
    seen := map[string]struct{}{}
    var out []string
    for _, it := range items {
        key := strings.TrimSpace(it)
        if _, ok := seen[key]; ok {
            continue
        }
        seen[key] = struct{}{}
        out = append(out, key)
    }
    return out
}
