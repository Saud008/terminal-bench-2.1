package routewin

import "github.com/terminus/xsnapctl/internal/model"

func RouteScore(rule model.RouteRule) int {
    if rule.Match.Path != "" {
        return 1_000_000 + len(rule.Match.Path)
    }
    return len(rule.Match.Prefix)
}

func SelectWinningRoutes(routes []model.RouteRule) []model.RouteRule {
    best := map[string]model.RouteRule{}
    for _, rule := range routes {
        cur, ok := best[rule.Cluster]
        if !ok {
            best[rule.Cluster] = rule
            continue
        }
        if RouteScore(rule) > RouteScore(cur) {
            best[rule.Cluster] = rule
        } else if RouteScore(rule) == RouteScore(cur) && rule.Precedence > cur.Precedence {
            best[rule.Cluster] = rule
        }
    }
    out := make([]model.RouteRule, 0, len(best))
    for _, rule := range best {
        out = append(out, rule)
    }
    return out
}
