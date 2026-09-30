// Package registry loads the package index pinwheel resolves against: one
// JSON file per package in a directory.
package registry

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/brightloom/pinwheel/internal/semver"
)

// Release is one published version of a package.
type Release struct {
	Version      string            `json:"version"`
	Published    time.Time         `json:"published"`
	Yanked       bool              `json:"yanked"`
	Dependencies map[string]string `json:"dependencies"`

	// Parsed is Version parsed; Index is the release's position in its file.
	Parsed semver.Version `json:"-"`
	Index  int            `json:"-"`
}

// Package is every release of one package, in file order.
type Package struct {
	Name     string    `json:"name"`
	Releases []Release `json:"versions"`
}

// Registry is a loaded registry directory.
type Registry struct {
	packages map[string]*Package
}

// Load reads every *.json file in dir.
func Load(dir string) (*Registry, error) {
	paths, err := filepath.Glob(filepath.Join(dir, "*.json"))
	if err != nil {
		return nil, err
	}
	if len(paths) == 0 {
		if _, err := os.Stat(dir); err != nil {
			return nil, fmt.Errorf("registry: %w", err)
		}
	}
	sort.Strings(paths)
	reg := &Registry{packages: map[string]*Package{}}
	for _, path := range paths {
		pkg, err := loadPackage(path)
		if err != nil {
			return nil, err
		}
		if _, dup := reg.packages[pkg.Name]; dup {
			return nil, fmt.Errorf("registry: package %q is defined twice", pkg.Name)
		}
		reg.packages[pkg.Name] = pkg
	}
	return reg, nil
}

func loadPackage(path string) (*Package, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("registry: %w", err)
	}
	var pkg Package
	dec := json.NewDecoder(strings.NewReader(string(data)))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&pkg); err != nil {
		return nil, fmt.Errorf("registry: %s: %w", filepath.Base(path), err)
	}
	if pkg.Name == "" {
		return nil, fmt.Errorf("registry: %s: missing package name", filepath.Base(path))
	}
	for i := range pkg.Releases {
		rel := &pkg.Releases[i]
		v, err := semver.Parse(rel.Version)
		if err != nil {
			return nil, fmt.Errorf("registry: %s: %w", pkg.Name, err)
		}
		for _, prev := range pkg.Releases[:i] {
			if prev.Parsed.Equal(v) {
				return nil, fmt.Errorf("registry: %s: version %s is listed twice", pkg.Name, rel.Version)
			}
		}
		if rel.Published.IsZero() {
			return nil, fmt.Errorf("registry: %s %s: missing published time", pkg.Name, rel.Version)
		}
		if rel.Dependencies == nil {
			rel.Dependencies = map[string]string{}
		}
		rel.Parsed = v
		rel.Index = i
	}
	return &pkg, nil
}

// Package returns the named package.
func (r *Registry) Package(name string) (*Package, bool) {
	p, ok := r.packages[name]
	return p, ok
}
