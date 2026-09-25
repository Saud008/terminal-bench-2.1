package export

import (
	"github.com/terminus/pulumi-dep-export/internal/graph"
	"github.com/terminus/pulumi-dep-export/internal/model"
)

// BuildReport loads staged adjacency but rebuilds the resource slice from the snapshot.
func BuildReport(snap model.Snapshot, ledgerPath string) model.ExportReport {
	ledger, err := graph.LoadLedger(ledgerPath)
	if err != nil {
		panic(err)
	}
	resources := graph.FlattenComponents(snap.Resources)
	orderURNs := graph.TopoOrder(resources, ledger.Adjacency)

	byURN := map[string]model.Resource{}
	for _, r := range snap.Resources {
		byURN[r.URN] = r
	}

	order := make([]model.OrderEntry, 0, len(orderURNs))
	providers := 0
	components := 0
	dbrPairs := 0
	for _, urn := range orderURNs {
		r := byURN[urn]
		if model.IsProvider(r) {
			providers++
		}
		if r.Component {
			components++
		}
		if r.DeleteBeforeReplace && r.Replaces != "" {
			dbrPairs++
		}
		order = append(order, model.OrderEntry{
			URN:       r.URN,
			Type:      r.Type,
			Component: r.Component,
			Depth:     depth(urn, byURN),
		})
	}

	return model.ExportReport{
		Stack: snap.Stack,
		Order: order,
		Stats: model.ExportStats{
			Resources:                len(order),
			ProviderNodes:            providers,
			ComponentRoots:           components,
			DeleteBeforeReplacePairs: dbrPairs,
		},
	}
}

func depth(urn string, byURN map[string]model.Resource) int {
	d := 0
	cur := urn
	for {
		r, ok := byURN[cur]
		if !ok || r.Parent == "" {
			break
		}
		if _, ok := byURN[r.Parent]; !ok {
			break
		}
		d++
		cur = r.Parent
	}
	return d
}
