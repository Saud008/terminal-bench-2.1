package pwcore

import "sort"

func IsWellKnown(c string) bool {
	asn := 0
	n := 0
	for i := 0; i < len(c); i++ {
		if c[i] == ':' {
			break
		}
		if c[i] < '0' || c[i] > '9' {
			return false
		}
		asn = asn*10 + int(c[i]-'0')
		n++
	}
	if n == 0 {
		return false
	}
	return asn == 0 || asn == 65535
}

func RewriteCommunities(comms []string, m map[string]string) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := append([]string{}, comms...)
	for _, k := range keys {
		to := m[k]
		for i, c := range out {
			if !IsWellKnown(c) && c == k {
				out[i] = to
			}
		}
	}
	return out
}
