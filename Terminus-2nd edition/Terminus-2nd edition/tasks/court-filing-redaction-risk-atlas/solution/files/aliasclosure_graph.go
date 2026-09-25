package partygraph

import (
    "sort"
    "strings"

    "github.com/terminus/filingatlas/internal/model"
)

func ResolveAliases(parties []model.Party) map[string][]string {
    graph := map[string]map[string]struct{}{}
    for _, p := range parties {
        graph[p.ID] = map[string]struct{}{}
        for _, alias := range p.Aliases {
            graph[p.ID][alias] = struct{}{}
        }
    }
    changed := true
    for changed {
        changed = false
        for _, p := range parties {
            pid := p.ID
            for alias := range graph[pid] {
                for _, other := range parties {
                    if strings.EqualFold(other.Name, alias) || aliasInList(alias, other.Aliases) {
                        for _, a := range other.Aliases {
                            if _, seen := graph[pid][a]; !seen {
                                graph[pid][a] = struct{}{}
                                changed = true
                            }
                        }
                        if _, seen := graph[pid][other.Name]; !seen {
                            graph[pid][other.Name] = struct{}{}
                            changed = true
                        }
                    }
                }
            }
        }
    }
    out := map[string][]string{}
    for id, aliases := range graph {
        list := make([]string, 0, len(aliases))
        for a := range aliases {
            list = append(list, a)
        }
        sort.Strings(list)
        out[id] = list
    }
    return out
}

func aliasInList(alias string, aliases []string) bool {
    for _, a := range aliases {
        if strings.EqualFold(a, alias) {
            return true
        }
    }
    return false
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
