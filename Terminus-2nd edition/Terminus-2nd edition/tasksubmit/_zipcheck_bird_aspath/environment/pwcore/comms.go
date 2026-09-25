package pwcore

import "sort"

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
			if c == k {
				out[i] = to
			}
		}
	}
	return out
}

func IsWellKnown(c string) bool {
	asn := 0
	for i := 0; i < len(c); i++ {
		if c[i] == ':' {
			break
		}
		asn = asn*10 + int(c[i]-'0')
	}
	return asn == 0 || asn == 65535
}
