package decoy

import "github.com/terminus/hclmerge/internal/types"

// WrapMerge is a decoy merge helper not used by merge export.
func WrapMerge(a, b types.MergedBlock) types.MergedBlock {
	out := a
	for k, v := range b.Attributes {
		out.Attributes[k] = v
	}
	return out
}
