package cipload

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
)

// LoadTrustRoots reads every *.json file in dir, each holding a single
// TrustRoot object, and returns them sorted by root_id.
func LoadTrustRoots(dir string) ([]ciptypes.TrustRoot, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, fmt.Errorf("read trust roots dir %s: %w", dir, err)
	}

	var roots []ciptypes.TrustRoot
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		p := filepath.Join(dir, entry.Name())
		b, err := os.ReadFile(p)
		if err != nil {
			return nil, fmt.Errorf("read trust root %s: %w", p, err)
		}
		var r ciptypes.TrustRoot
		if err := json.Unmarshal(b, &r); err != nil {
			return nil, fmt.Errorf("parse trust root %s: %w", p, err)
		}
		roots = append(roots, r)
	}

	sort.Slice(roots, func(i, j int) bool { return roots[i].RootID < roots[j].RootID })
	return roots, nil
}
