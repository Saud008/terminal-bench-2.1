// Package lockfile builds and writes pin.lock.
package lockfile

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/brightloom/pinwheel/internal/manifest"
	"github.com/brightloom/pinwheel/internal/resolve"
)

// FileName is the lock's name inside a project directory.
const FileName = "pin.lock"

// FormatVersion is written as lockfileVersion.
const FormatVersion = 1

// Lock is the document written to pin.lock. Field order is the output order.
type Lock struct {
	LockfileVersion int              `json:"lockfileVersion"`
	Name            string           `json:"name"`
	Packages        map[string]Entry `json:"packages"`
}

// Entry is one locked package.
type Entry struct {
	Version      string            `json:"version"`
	RequiredBy   []string          `json:"requiredBy"`
	Dependencies map[string]string `json:"dependencies"`
}

// Build turns a resolution into a lock.
func Build(m *manifest.Manifest, res *resolve.Result) *Lock {
	lock := &Lock{LockfileVersion: FormatVersion, Name: m.Name, Packages: map[string]Entry{}}
	for name, rel := range res.Selected {
		deps := make(map[string]string, len(rel.Dependencies))
		for k, v := range rel.Dependencies {
			deps[k] = v
		}
		lock.Packages[name] = Entry{
			Version:      rel.Version,
			RequiredBy:   requiredBy(res.Constraints[name]),
			Dependencies: deps,
		}
	}
	return lock
}

func requiredBy(cons []resolve.Constraint) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, c := range cons {
		if !seen[c.From] {
			seen[c.From] = true
			out = append(out, c.From)
		}
	}
	sort.Strings(out)
	return out
}

// Encode renders the lock exactly as it is stored on disk.
func Encode(l *Lock) ([]byte, error) {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if err := enc.Encode(l); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// Write stores the lock at path, replacing any previous file atomically.
func Write(path string, l *Lock) error {
	data, err := Encode(l)
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".pin.lock-*")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Chmod(tmp.Name(), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}
