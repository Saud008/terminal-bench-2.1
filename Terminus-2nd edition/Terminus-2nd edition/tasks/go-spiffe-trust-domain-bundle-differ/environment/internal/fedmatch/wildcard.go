package fedmatch

import "strings"

func MatchAllowlist(candidate string, allowlist []string) []string {
    host := strings.ToLower(strings.TrimSpace(candidate))
    var out []string
    for _, pat := range allowlist {
        if strings.ToLower(strings.TrimSpace(pat)) == host {
            out = append(out, pat)
        }
    }
    return out
}

func FilterFederation(bundleHost string, allowlist []string) []string {
    return MatchAllowlist(bundleHost, allowlist)
}
