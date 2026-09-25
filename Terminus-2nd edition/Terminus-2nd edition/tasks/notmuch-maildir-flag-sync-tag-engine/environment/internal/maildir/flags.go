package maildir

import "sort"

// CanonicalOrder is FSRDT per /app/docs/maildir-flag-order.md
var CanonicalOrder = []byte{'F', 'S', 'R', 'T', 'D'}

// NormalizeFlags canonicalizes Maildir flag letters read from filenames.
func NormalizeFlags(raw string) string {
	if raw == "" {
		return ""
	}
	set := map[byte]bool{}
	for i := 0; i < len(raw); i++ {
		set[raw[i]] = true
	}
	letters := make([]byte, 0, len(set))
	for c := range set {
		letters = append(letters, c)
	}
	sort.Slice(letters, func(i, j int) bool { return letters[i] < letters[j] })
	return string(letters)
}

func FlagsFromTags(tags []string) string {
	present := map[byte]bool{}
	for _, t := range tags {
		switch t {
		case "flagged":
			present['F'] = true
		case "seen":
			present['S'] = true
		case "replied":
			present['R'] = true
		case "trashed":
			present['T'] = true
		case "draft":
			present['D'] = true
		}
	}
	raw := make([]byte, 0, 5)
	for _, c := range CanonicalOrder {
		if present[c] {
			raw = append(raw, c)
		}
	}
	return NormalizeFlags(string(raw))
}
