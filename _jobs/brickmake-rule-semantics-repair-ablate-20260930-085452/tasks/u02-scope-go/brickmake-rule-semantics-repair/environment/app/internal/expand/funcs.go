package expand

import (
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	"brickmake/internal/diag"
	"brickmake/internal/text"
)

// function describes a builtin. Lazy functions receive their arguments
// unexpanded.
type function struct {
	min, max int
	lazy     bool
	run      func(e *Expander, args []string, sc *Scope) string
}

var functions map[string]function

func init() {
	functions = map[string]function{
		"subst":      {3, 3, false, fnSubst},
		"patsubst":   {3, 3, false, func(_ *Expander, a []string, _ *Scope) string { return text.Patsubst(a[0], a[1], a[2]) }},
		"strip":      {1, 1, false, func(_ *Expander, a []string, _ *Scope) string { return text.Join(text.Fields(a[0])) }},
		"findstring": {2, 2, false, fnFindstring},
		"filter":     {2, 2, false, func(_ *Expander, a []string, _ *Scope) string { return filter(a[0], a[1], true) }},
		"filter-out": {2, 2, false, func(_ *Expander, a []string, _ *Scope) string { return filter(a[0], a[1], false) }},
		"sort":       {1, 1, false, fnSort},
		"word":       {2, 2, false, fnWord},
		"wordlist":   {3, 3, false, fnWordlist},
		"words":      {1, 1, false, func(_ *Expander, a []string, _ *Scope) string { return strconv.Itoa(len(text.Fields(a[0]))) }},
		"firstword":  {1, 1, false, fnFirstword},
		"lastword":   {1, 1, false, fnLastword},
		"dir":        {1, 1, false, eachWord(text.Dir)},
		"notdir":     {1, 1, false, eachWord(text.Notdir)},
		"suffix":     {1, 1, false, fnSuffix},
		"basename":   {1, 1, false, eachWord(text.Basename)},
		"addsuffix":  {2, 2, false, fnAddsuffix},
		"addprefix":  {2, 2, false, fnAddprefix},
		"join":       {2, 2, false, fnJoin},
		"wildcard":   {1, 1, false, fnWildcard},
		"foreach":    {3, 3, true, fnForeach},
		"if":         {2, 3, true, fnIf},
		"or":         {1, 0, true, fnOr},
		"and":        {1, 0, true, fnAnd},
		"call":       {1, 0, false, fnCall},
		"origin":     {1, 1, false, fnOrigin},
		"flavor":     {1, 1, false, fnFlavor},
		"value":      {1, 1, false, fnValue},
		"info":       {0, 1, false, fnInfo},
		"warning":    {0, 1, false, fnWarning},
		"error":      {0, 1, false, fnError},
		"shell":      {1, 1, false, fnShell},
	}
}

func (e *Expander) call(fn function, name, body string, open, close byte, sc *Scope) string {
	args := splitArgs(body, open, close, fn.max)
	if len(args) < fn.min {
		diag.Failf(e.Pos, "insufficient number of arguments (%d) to function '%s'", len(args), name)
	}
	if !fn.lazy {
		for i, a := range args {
			args[i] = e.Expand(a, sc)
		}
	}
	return fn.run(e, args, sc)
}

func eachWord(f func(string) string) func(*Expander, []string, *Scope) string {
	return func(_ *Expander, a []string, _ *Scope) string {
		words := text.Fields(a[0])
		for i, w := range words {
			words[i] = f(w)
		}
		return text.Join(words)
	}
}

func fnSubst(_ *Expander, a []string, _ *Scope) string {
	if a[0] == "" {
		return a[2] + a[1]
	}
	return strings.ReplaceAll(a[2], a[0], a[1])
}

func fnFindstring(_ *Expander, a []string, _ *Scope) string {
	if strings.Contains(a[1], a[0]) {
		return a[0]
	}
	return ""
}

func filter(patterns, s string, keep bool) string {
	var pats []text.Pattern
	for _, p := range text.Fields(patterns) {
		pats = append(pats, text.ParsePattern(p))
	}
	var out []string
	for _, w := range text.Fields(s) {
		hit := false
		for _, p := range pats {
			if _, ok := p.Match(w); ok {
				hit = true
				break
			}
		}
		if hit == keep {
			out = append(out, w)
		}
	}
	return text.Join(out)
}

func fnSort(_ *Expander, a []string, _ *Scope) string {
	words := text.Fields(a[0])
	sort.Strings(words)
	return text.Join(text.Uniq(words))
}

func (e *Expander) number(s, fn, which string) int {
	s = text.TrimSpace(s)
	n, err := strconv.Atoi(s)
	if err != nil || s == "" {
		diag.Failf(e.Pos, "non-numeric %s argument to '%s' function: '%s'", which, fn, s)
	}
	return n
}

func fnWord(e *Expander, a []string, _ *Scope) string {
	n := e.number(a[0], "word", "first")
	if n <= 0 {
		diag.Failf(e.Pos, "first argument to 'word' function must be greater than 0")
	}
	words := text.Fields(a[1])
	if n > len(words) {
		return ""
	}
	return words[n-1]
}

func fnWordlist(e *Expander, a []string, _ *Scope) string {
	s := e.number(a[0], "wordlist", "first")
	end := e.number(a[1], "wordlist", "second")
	if s <= 0 {
		diag.Failf(e.Pos, "invalid first argument to 'wordlist' function: '%d'", s)
	}
	if end < 0 {
		diag.Failf(e.Pos, "invalid second argument to 'wordlist' function: '%d'", end)
	}
	words := text.Fields(a[2])
	if end > len(words) {
		end = len(words)
	}
	if s > end {
		return ""
	}
	return text.Join(words[s-1 : end])
}

func fnFirstword(_ *Expander, a []string, _ *Scope) string {
	if w := text.Fields(a[0]); len(w) > 0 {
		return w[0]
	}
	return ""
}

func fnLastword(_ *Expander, a []string, _ *Scope) string {
	if w := text.Fields(a[0]); len(w) > 0 {
		return w[len(w)-1]
	}
	return ""
}

func fnSuffix(_ *Expander, a []string, _ *Scope) string {
	var out []string
	for _, w := range text.Fields(a[0]) {
		if s := text.Suffix(w); s != "" {
			out = append(out, s)
		}
	}
	return text.Join(out)
}

func fnAddsuffix(_ *Expander, a []string, _ *Scope) string {
	words := text.Fields(a[1])
	for i, w := range words {
		words[i] = w + a[0]
	}
	return text.Join(words)
}

func fnAddprefix(_ *Expander, a []string, _ *Scope) string {
	words := text.Fields(a[1])
	for i, w := range words {
		words[i] = a[0] + w
	}
	return text.Join(words)
}

func fnJoin(_ *Expander, a []string, _ *Scope) string {
	x, y := text.Fields(a[0]), text.Fields(a[1])
	n := len(x)
	if len(y) > n {
		n = len(y)
	}
	out := make([]string, n)
	for i := range out {
		if i < len(x) {
			out[i] = x[i]
		}
		if i < len(y) {
			out[i] += y[i]
		}
	}
	return text.Join(out)
}

func fnWildcard(_ *Expander, a []string, _ *Scope) string {
	var out []string
	for _, p := range text.Fields(a[0]) {
		matches, err := filepath.Glob(p)
		if err != nil {
			continue
		}
		sort.Strings(matches)
		out = append(out, matches...)
	}
	return text.Join(out)
}
