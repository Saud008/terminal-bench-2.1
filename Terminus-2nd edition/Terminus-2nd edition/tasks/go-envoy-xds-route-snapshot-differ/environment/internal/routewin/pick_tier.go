package routewin

import "github.com/terminus/xsnapctl/internal/model"

func RouteScore(rule model.RouteRule) int {
    if rule.Match.Path != "" {
        return len(rule.Match.Path)
    }
    return len(rule.Match.Prefix)
}

// SelectWinningRoutes collapses duplicate cluster routes using precedence score.
func SelectWinningRoutes(routes []model.RouteRule) []model.RouteRule {
    best := map[string]model.RouteRule{}
    for _, rule := range routes {
        cur, ok := best[rule.Cluster]
        if !ok || RouteScore(rule) < RouteScore(cur) {
            best[rule.Cluster] = rule
        }
    }
    out := make([]model.RouteRule, 0, len(best))
    for _, rule := range best {
        out = append(out, rule)
    }
    return out
}
