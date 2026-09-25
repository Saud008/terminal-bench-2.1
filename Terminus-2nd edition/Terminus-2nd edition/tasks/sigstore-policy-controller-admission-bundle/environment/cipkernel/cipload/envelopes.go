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

// LoadEnvelopes reads every *.json file in dir, each holding a single
// Envelope object, and returns them sorted by envelope_id.
func LoadEnvelopes(dir string) ([]ciptypes.Envelope, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, fmt.Errorf("read envelopes dir %s: %w", dir, err)
	}

	var envelopes []ciptypes.Envelope
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		p := filepath.Join(dir, entry.Name())
		b, err := os.ReadFile(p)
		if err != nil {
			return nil, fmt.Errorf("read envelope %s: %w", p, err)
		}
		var e ciptypes.Envelope
		if err := json.Unmarshal(b, &e); err != nil {
			return nil, fmt.Errorf("parse envelope %s: %w", p, err)
		}
		envelopes = append(envelopes, e)
	}

	sort.Slice(envelopes, func(i, j int) bool { return envelopes[i].EnvelopeID < envelopes[j].EnvelopeID })
	return envelopes, nil
}
