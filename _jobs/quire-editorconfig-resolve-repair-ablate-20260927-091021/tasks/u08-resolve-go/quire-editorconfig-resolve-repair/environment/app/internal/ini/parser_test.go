package ini

import (
	"reflect"
	"strings"
	"testing"
)

type prop struct{ section, name, value string }

func parse(t *testing.T, text string) ([]prop, int) {
	t.Helper()
	var got []prop
	line := Parse(strings.NewReader(text), func(s, n, v string) {
		got = append(got, prop{s, n, v})
	})
	return got, line
}

func TestParseSections(t *testing.T) {
	got, line := parse(t, "root = true\n; comment\n\n[*.go]\nindent_style = tab\n  [Makefile]  \nx:1\n")
	want := []prop{{"", "root", "true"}, {"*.go", "indent_style", "tab"}, {"Makefile", "x", "1"}}
	if line != 0 || !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v line %d", got, line)
	}
}

func TestParseFirstErrorLine(t *testing.T) {
	_, line := parse(t, "[*]\na = 1\nnot a property\nb = 2\n[broken\n")
	if line != 3 {
		t.Fatalf("error line %d, want 3", line)
	}
}

func TestParseLongName(t *testing.T) {
	got, _ := parse(t, "[*]\n"+strings.Repeat("n", MaxPropertyName+1)+" = 1\nok = 2\n")
	if len(got) != 1 || got[0].name != "ok" {
		t.Fatalf("got %v", got)
	}
}
