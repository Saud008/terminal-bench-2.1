package ingest

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/hclmerge/internal/parse"
	"github.com/terminus/hclmerge/internal/staging"
	"github.com/terminus/hclmerge/internal/types"
)

// IngestDirectory parses all .hcl files in dir and writes staging.
func IngestDirectory(dir, stagePath string) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return err
	}
	var paths []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		if strings.HasSuffix(e.Name(), ".hcl") {
			paths = append(paths, filepath.Join(dir, e.Name()))
		}
	}
	sort.Strings(paths)

	var fragments []types.Fragment
	for i, p := range paths {
		fr, err := parse.ParseFragment(p, i+1)
		if err != nil {
			return fmt.Errorf("%s: %w", p, err)
		}
		fragments = append(fragments, *fr)
	}
	st := &types.StageFile{Fragments: fragments}
	return staging.Save(stagePath, st)
}
