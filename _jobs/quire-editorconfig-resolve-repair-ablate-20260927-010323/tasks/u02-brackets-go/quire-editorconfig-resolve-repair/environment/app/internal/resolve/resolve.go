// Package resolve computes the EditorConfig properties for one file.
package resolve

import (
	"strings"

	"quire/internal/ctext"
	"quire/internal/glob"
	"quire/internal/ini"
	"quire/internal/props"
	"quire/internal/version"
)

// DefaultConfName is the EditorConfig file name used without -f.
const DefaultConfName = ".editorconfig"

// Options control one resolution.
type Options struct {
	ConfName string
	Version  version.Version
}

type walker struct {
	full  string
	dir   string
	store props.Store
}

// File returns the properties for the file at full, in output order.
func File(full string, o Options) ([]props.Pair, error) {
	if o.Version.Compare(version.Current) > 0 {
		return nil, ErrVersionTooNew
	}
	if !strings.HasPrefix(full, "/") {
		return nil, ErrNotFullPath
	}
	w := &walker{full: full}
	for _, conf := range configPaths(full, o.ConfName) {
		w.dir = dirOf(conf)
		line, err := ini.ParseFile(conf, w.property)
		if err != nil {
			continue
		}
		if line != 0 {
			return nil, &ParseError{Line: line, File: conf}
		}
	}
	props.Derive(&w.store, o.Version)
	return w.store.Pairs(), nil
}

// property handles one name/value pair from the file in w.dir. root = true
// discards everything collected from the files above.
func (w *walker) property(section, name, value string) {
	if ctext.EqualFold(name, "root") && ctext.EqualFold(value, "true") {
		w.store.Reset()
		return
	}
	if glob.Match(sectionPattern(w.dir, section), w.full) {
		w.store.Set(name, value)
	}
}
