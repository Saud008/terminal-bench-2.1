package digest

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sort"

	"github.com/terminus/brat-consensus-exporter/internal/model"
)

func SpanKey(s model.ConsensusSpan) string {
	return s.DocID + ":" + s.Label + ":" + itoa(s.Start) + "-" + itoa(s.End)
}

func RelKey(r model.ConsensusRelation) string {
	return r.DocID + ":" + r.Arg1Span + "->" + r.Arg2Span + ":" + r.Type
}

func itoa(v int) string {
	return fmt.Sprintf("%d", v)
}

func ConsensusDigest(projectID string, spans []model.ConsensusSpan, rels []model.ConsensusRelation) string {
	spanKeys := make([]string, 0, len(spans))
	for _, s := range spans {
		spanKeys = append(spanKeys, SpanKey(s))
	}
	sort.Strings(spanKeys)
	relKeys := make([]string, 0, len(rels))
	for _, r := range rels {
		relKeys = append(relKeys, RelKey(r))
	}
	sort.Strings(relKeys)
	// encoding/json map keys are sorted; disable HTML escaping so "->" stays literal
	// (matches Python json.dumps(..., sort_keys=True, separators=(",", ":"))).
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(map[string]interface{}{
		"project_id": projectID,
		"relations":  relKeys,
		"spans":      spanKeys,
	})
	body := bytes.TrimRight(buf.Bytes(), "\n")
	sum := sha256.Sum256(body)
	return "sha256:" + hex.EncodeToString(sum[:])
}
