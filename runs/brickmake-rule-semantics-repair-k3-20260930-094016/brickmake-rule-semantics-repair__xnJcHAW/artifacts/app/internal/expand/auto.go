package expand

import (
	"strings"

	"brickmake/internal/text"
)

// Auto holds the automatic variables of one recipe or of one secondary
// expansion.
type Auto struct {
	Target string   // $@
	First  string   // $<
	All    []string // $^
	Plus   []string // $+
	Order  []string // $|
	Newer  []string // $?
	Stem   string   // $*
}

// Names lists the automatic variables that $(origin) reports as
// "automatic".
var autoNames = map[string]bool{"@": true, "<": true, "^": true, "+": true, "|": true, "?": true, "*": true}

func IsAutomatic(name string) bool {
	if autoNames[name] {
		return true
	}
	return len(name) == 2 && autoNames[name[:1]] && (name[1] == 'D' || name[1] == 'F')
}

func (a *Auto) raw(c byte) (string, bool) {
	switch c {
	case '@':
		return a.Target, true
	case '<':
		return a.First, true
	case '^':
		return text.Join(a.All), true
	case '+':
		return text.Join(a.Plus), true
	case '|':
		return text.Join(a.Order), true
	case '?':
		return text.Join(a.Newer), true
	case '*':
		return a.Stem, true
	}
	return "", false
}

// Value returns the value of an automatic variable, including the D and F
// variants.
func (a *Auto) Value(name string) (string, bool) {
	switch len(name) {
	case 1:
		return a.raw(name[0])
	case 2:
		v, ok := a.raw(name[0])
		if !ok || (name[1] != 'D' && name[1] != 'F') {
			return "", false
		}
		words := text.Fields(v)
		for i, w := range words {
			if name[1] == 'F' {
				words[i] = text.Notdir(w)
				continue
			}
			d := text.Dir(w)
			if len(d) > 1 {
				d = strings.TrimSuffix(d, "/")
			} else if d == "./" {
				d = "."
			}
			words[i] = d
		}
		return text.Join(words), true
	}
	return "", false
}
