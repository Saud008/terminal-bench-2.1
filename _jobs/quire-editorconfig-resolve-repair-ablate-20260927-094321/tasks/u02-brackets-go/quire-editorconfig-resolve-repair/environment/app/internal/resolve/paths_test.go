package resolve

import (
	"reflect"
	"testing"
)

func TestConfigPaths(t *testing.T) {
	got := configPaths("/a/b/c.txt", ".editorconfig")
	want := []string{"/.editorconfig", "/a/.editorconfig", "/a/b/.editorconfig"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v", got)
	}
	if d := dirOf("/a/b/.editorconfig"); d != "/a/b" {
		t.Fatalf("dirOf = %q", d)
	}
}
