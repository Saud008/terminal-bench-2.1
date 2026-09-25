package exhibitlink

import (
    "regexp"
    "strings"
)

var exhibitRe = regexp.MustCompile(`(?i)Exhibit\s+(\d+)(?:-([A-Za-z]+))?(?:\s+(IV|III|II|I|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I))?`)

func ParseExhibitRefs(text string) []string {
    var out []string
    for _, m := range exhibitRe.FindAllStringSubmatch(text, -1) {
        if len(m) > 1 {
            ref := "Exhibit " + m[1]
            if len(m) > 2 && m[2] != "" {
                ref = ref + "-" + m[2]
            }
            if len(m) > 3 && m[3] != "" {
                ref = ref + " " + m[3]
            }
            out = append(out, ref)
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
