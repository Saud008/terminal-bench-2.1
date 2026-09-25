package merge

import (
	"sort"

	"github.com/terminus/hclmerge/internal/types"
)

// MergeFragments combines fragments in order into one merged block (attributes only).
func MergeFragments(fragments []types.Fragment) types.MergedBlock {
	if len(fragments) == 0 {
		return types.MergedBlock{Attributes: map[string]interface{}{}}
	}
	sort.SliceStable(fragments, func(i, j int) bool {
		return fragments[i].Order < fragments[j].Order
	})
	base := fragments[0]
	out := types.MergedBlock{
		BlockType:  base.BlockType,
		Labels:     append([]string{}, base.Labels...),
		Attributes: map[string]interface{}{},
	}
	for k, v := range base.Attributes {
		out.Attributes[k] = v
	}
	for _, fr := range fragments[1:] {
		out = applyShallow(out, fr)
	}
	return out
}

// ApplyAllOverrides applies merge_override maps in fragment order.
func ApplyAllOverrides(block types.MergedBlock, fragments []types.Fragment) types.MergedBlock {
	sort.SliceStable(fragments, func(i, j int) bool {
		return fragments[i].Order < fragments[j].Order
	})
	for _, fr := range fragments {
		block = applyOverrides(block, fr.MergeOverrides)
	}
	return block
}

// applyShallow merges fragment attributes at the top level.
func applyShallow(block types.MergedBlock, fr types.Fragment) types.MergedBlock {
	for k, v := range fr.Attributes {
		block.Attributes[k] = v
	}
	return block
}

// applyOverrides merges merge_override maps into block attributes.
func applyOverrides(block types.MergedBlock, overrides map[string]interface{}) types.MergedBlock {
	for k, v := range overrides {
		if v == nil {
			continue
		}
		block.Attributes[k] = v
	}
	return block
}

// NestAttributes converts dot keys into nested maps for export JSON.
func NestAttributes(flat map[string]interface{}) map[string]interface{} {
	out := map[string]interface{}{}
	for k, v := range flat {
		parts := splitDot(k)
		cursor := out
		for i := 0; i < len(parts)-1; i++ {
			next, ok := cursor[parts[i]].(map[string]interface{})
			if !ok {
				next = map[string]interface{}{}
				cursor[parts[i]] = next
			}
			cursor = next
		}
		cursor[parts[len(parts)-1]] = v
	}
	return out
}

func splitDot(s string) []string {
	var parts []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '.' {
			parts = append(parts, s[start:i])
			start = i + 1
		}
	}
	parts = append(parts, s[start:])
	return parts
}
