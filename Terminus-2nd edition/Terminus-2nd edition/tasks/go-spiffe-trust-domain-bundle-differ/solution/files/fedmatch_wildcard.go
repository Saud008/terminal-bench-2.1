package fedmatch

import "strings"

func wildcardMatch(host, pattern string) bool {
    host = strings.ToLower(strings.TrimSpace(host))
    pat := strings.ToLower(strings.TrimSpace(pattern))
    if strings.HasPrefix(pat, "*.") {
        suffix := pat[1:]
        return strings.HasSuffix(host, suffix) || host == pat[2:]
    }
    return host == pat
}

func MatchAllowlist(candidate string, allowlist []string) []string {
    var out []string
    for _, pat := range allowlist {
        if wildcardMatch(candidate, pat) {
            out = append(out, pat)
        }
    }
    return out
}

func FilterFederation(bundleHost string, allowlist []string) []string {
    return MatchAllowlist(bundleHost, allowlist)
}
