package export

import (
	"sort"
	"strings"

	"github.com/terminus/kongadmit/internal/merge"
	"github.com/terminus/kongadmit/internal/model"
)

func BuildOpenAPI(routes map[string]model.Route, services map[string]model.Service) model.OpenAPISpec {
	paths := make(map[string]any)
	type routeEntry struct {
		path string
		rt   model.Route
	}
	var ordered []routeEntry
	for _, rt := range routes {
		if len(rt.Paths) == 0 {
			continue
		}
		ordered = append(ordered, routeEntry{path: rt.Paths[0], rt: rt})
	}
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].path < ordered[j].path
	})
	for _, item := range ordered {
		rt := item.rt
		svc, ok := services[rt.Service]
		if !ok {
			continue
		}
		pathItem, _ := paths[item.path].(map[string]any)
		if pathItem == nil {
			pathItem = make(map[string]any)
			paths[item.path] = pathItem
		}
		for _, method := range rt.Methods {
			m := strings.ToLower(method)
			op := map[string]any{
				"operationId": rt.Name,
				"responses": map[string]any{
					"200": map[string]any{
						"description": "upstream response",
						"headers":     stageHeaders(svc, rt),
					},
				},
			}
			pathItem[m] = op
		}
	}
	return model.OpenAPISpec{
		OpenAPI: "3.0.3",
		Info: map[string]string{
			"title":   "kongadmit export",
			"version": "1.0.0",
		},
		Paths: paths,
	}
}

func stageHeaders(svc model.Service, rt model.Route) map[string]any {
	headers := make(map[string]any)
	for _, name := range StagedPluginHeaders(svc, rt) {
		headers[name] = map[string]any{"schema": map[string]string{"type": "string"}}
	}
	return headers
}

func StagedPluginHeaders(svc model.Service, rt model.Route) []string {
	plugins := merge.EffectivePlugins(svc, rt)
	seen := make(map[string]bool)
	var out []string
	for _, pl := range plugins {
		switch pl.Name {
		case "response-transformer":
			add, _ := pl.Config["add"].(map[string]any)
			if add == nil {
				continue
			}
			headerLines, _ := add["headers"].([]any)
			for _, h := range headerLines {
				line, _ := h.(string)
				parts := strings.SplitN(line, ":", 2)
				if len(parts) == 2 {
					name := strings.TrimSpace(parts[0])
					if !seen[name] {
						seen[name] = true
						out = append(out, name)
					}
				}
			}
		case "rate-limiting":
			for _, name := range []string{"X-RateLimit-Limit", "X-RateLimit-Remaining"} {
				if !seen[name] {
					seen[name] = true
					out = append(out, name)
				}
			}
		}
	}
	return out
}
