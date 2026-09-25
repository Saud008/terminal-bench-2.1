package tags

import "sort"

var systemTags = map[string]bool{
	"flagged": true, "seen": true, "replied": true, "trashed": true, "draft": true, "inbox": true,
}

func FlagTags(flags string) []string {
	out := []string{}
	for _, c := range flags {
		switch c {
		case 'F':
			out = append(out, "flagged")
		case 'S':
			out = append(out, "seen")
		case 'R':
			out = append(out, "replied")
		case 'T':
			out = append(out, "trashed")
		case 'D':
			out = append(out, "draft")
		}
	}
	return out
}

// Merge combines X-Keywords, Maildir flag tags, and stored DB tags per tag-precedence.md.
func Merge(xKeywords, flagTags, dbTags []string) (tags []string, source string) {
	keywordBase := xKeywords
	source = "none"
	if len(dbTags) > 0 {
		kw := []string{}
		for _, t := range dbTags {
			if !systemTags[t] {
				kw = append(kw, t)
			}
		}
		if len(kw) > 0 {
			keywordBase = kw
			source = "db"
		}
	}
	if len(xKeywords) > 0 && source == "none" {
		keywordBase = xKeywords
		source = "x-keywords"
	}
	set := map[string]bool{}
	for _, t := range keywordBase {
		set[t] = true
	}
	for _, t := range flagTags {
		set[t] = true
	}
	for _, t := range dbTags {
		if systemTags[t] {
			set[t] = true
		}
	}
	out := make([]string, 0, len(set))
	for t := range set {
		out = append(out, t)
	}
	sort.Strings(out)
	return out, source
}
