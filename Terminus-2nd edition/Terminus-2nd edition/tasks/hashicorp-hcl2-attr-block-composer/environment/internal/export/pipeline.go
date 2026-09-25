package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"

	"github.com/terminus/hclmerge/internal/dynamic"
	"github.com/terminus/hclmerge/internal/merge"
	"github.com/terminus/hclmerge/internal/staging"
	"github.com/terminus/hclmerge/internal/types"
)

const (
	DefaultHCLPath       = "/app/output/merged.hcl"
	DefaultChecksumPath  = "/app/output/merge-checksum.txt"
)

// MergeExport reads staging and writes merged HCL + checksum.
func MergeExport(stagePath, hclPath, checksumPath string) error {
	st, err := staging.Load(stagePath)
	if err != nil {
		return err
	}
	if len(st.Fragments) == 0 {
		return fmt.Errorf("no fragments in staging")
	}

	merged := merge.MergeFragments(st.Fragments)
	expanded := dynamic.ExpandAll(merged, st.Fragments)
	merged = merge.ApplyAllOverrides(merged, st.Fragments)
	merged.Expanded = expanded

	labels := pickExportLabels(st.Fragments)
	merged.Labels = labels

	normalized := types.NormalizedExport{Blocks: []types.MergedBlock{merged}}
	_ = normalized
	hclText := renderHCL(merged)
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(hclPath, []byte(hclText), 0o644); err != nil {
		return err
	}
	sum := checksumFromHCL(hclText)
	return os.WriteFile(checksumPath, []byte(sum+"\n"), 0o644)
}

// pickExportLabels chooses label ordering for export.
func pickExportLabels(fragments []types.Fragment) []string {
	if len(fragments) == 0 {
		return nil
	}
	sort.SliceStable(fragments, func(i, j int) bool {
		return fragments[i].Order < fragments[j].Order
	})
	labels := append([]string{}, fragments[0].Labels...)
	sort.Strings(labels)
	return labels
}

func renderHCL(block types.MergedBlock) string {
	var b strings.Builder
	fmt.Fprintf(&b, "block %s %s {\n", block.BlockType, strings.Join(block.Labels, " "))
	nested := merge.NestAttributes(block.Attributes)
	renderNested(&b, nested, 1)
	for _, row := range block.Expanded {
		fmt.Fprintf(&b, "  dynamic %v {\n", row["dynamic"])
		for k, v := range row {
			if k == "dynamic" {
				continue
			}
			fmt.Fprintf(&b, "    %s = %q\n", k, v)
		}
		b.WriteString("  }\n")
	}
	b.WriteString("}\n")
	return b.String()
}

func renderNested(b *strings.Builder, m map[string]interface{}, indent int) {
	pad := strings.Repeat("  ", indent)
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		v := m[k]
		if child, ok := v.(map[string]interface{}); ok {
			fmt.Fprintf(b, "%s%s {\n", pad, k)
			renderNested(b, child, indent+1)
			fmt.Fprintf(b, "%s}\n", pad)
			continue
		}
		if v == nil {
			fmt.Fprintf(b, "%s%s = null\n", pad, k)
			continue
		}
		fmt.Fprintf(b, "%s%s = %q\n", pad, k, v)
	}
}

// checksumFromHCL derives the export digest from rendered HCL text.
func checksumFromHCL(hcl string) string {
	h := sha256.Sum256([]byte(strings.TrimSpace(hcl)))
	return hex.EncodeToString(h[:])
}

// CanonicalJSON returns normalized JSON bytes for reference tests.
func CanonicalJSON(norm types.NormalizedExport) ([]byte, error) {
	return json.Marshal(norm)
}
