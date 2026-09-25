package whtstack

import (
	"sort"

	"github.com/terminus/layerfuse/internal/types"
	"github.com/terminus/layerfuse/internal/whiteout"
)

// BuildStack merges staged members into a materialized view in layer order.
func BuildStack(members []types.TarMember) []types.StackEntry {
	byLayer := map[int][]types.TarMember{}
	maxLayer := 0
	for _, m := range members {
		byLayer[m.LayerIndex] = append(byLayer[m.LayerIndex], m)
		if m.LayerIndex > maxLayer {
			maxLayer = m.LayerIndex
		}
	}

	view := map[string]types.StackEntry{}
	layerOf := map[string]int{}

	for layer := 0; layer <= maxLayer; layer++ {
		layerMembers := byLayer[layer]
		sort.SliceStable(layerMembers, func(i, j int) bool {
			return layerMembers[i].Path < layerMembers[j].Path
		})
		var whiteouts []types.TarMember
		var opaques []types.TarMember
		for _, m := range layerMembers {
			switch m.Type {
			case types.MemberWhiteout:
				whiteouts = append(whiteouts, m)
			case types.MemberOpaque:
				opaques = append(opaques, m)
			case types.MemberFile, types.MemberDir:
				view[m.Path] = types.StackEntry{
					Path: m.Path,
					Type: m.Type,
					Mode: m.Mode,
					UID:  m.UID,
					GID:  m.GID,
				}
				layerOf[m.Path] = layer
			}
		}
		whiteout.ApplyWhiteouts(view, whiteouts)
		for _, op := range opaques {
			whiteout.ApplyOpaque(view, []types.TarMember{op}, layer, layerOf)
		}
	}

	out := make([]types.StackEntry, 0, len(view))
	for _, e := range view {
		out = append(out, e)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Path < out[j].Path })
	return out
}
