package partygraph

import "github.com/terminus/filingatlas/internal/model"

// ResolveAliases expands party alias edges for graph indexing.
func ResolveAliases(parties []model.Party) map[string][]string {
    out := map[string][]string{}
    for _, p := range parties {
        out[p.ID] = append([]string{}, p.Aliases...)
    }
    return out
}

func BuildGraph(scenario string, parties []model.Party) model.PartyGraph {
    nodes := []string{}
    edges := []model.AliasEdge{}
    for _, p := range parties {
        nodes = append(nodes, p.ID)
        for _, alias := range p.Aliases {
            edges = append(edges, model.AliasEdge{From: p.ID, To: alias})
        }
    }
    return model.PartyGraph{
        Scenario: scenario,
        Nodes:    nodes,
        Edges:    edges,
        Resolved: ResolveAliases(parties),
    }
}
