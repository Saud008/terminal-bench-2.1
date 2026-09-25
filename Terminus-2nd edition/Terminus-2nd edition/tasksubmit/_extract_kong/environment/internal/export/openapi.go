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
						"headers":     stageHeaders(rt),
					},
				},
			}
			_ = svc
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

func stageHeaders(rt model.Route) map[string]any {
	headers := make(map[string]any)
	for _, tag := range rt.Tags {
		headers["X-Route-Tag-"+tag] = map[string]any{"schema": map[string]string{"type": "string"}}
	}
	return headers
}

func StagedPluginHeaders(svc model.Service, rt model.Route) []string {
	plugins := merge.EffectivePlugins(svc, rt)
	var out []string
	for _, pl := range plugins {
		switch pl.Name {
		case "response-transformer":
			add, _ := pl.Config["add"].(map[string]any)
			if add == nil {
				continue
			}
			headers, _ := add["headers"].([]any)
			for _, h := range headers {
				line, _ := h.(string)
				parts := strings.SplitN(line, ":", 2)
				if len(parts) == 2 {
					out = append(out, strings.TrimSpace(parts[0]))
				}
			}
		case "rate-limiting":
			out = append(out, "X-RateLimit-Limit", "X-RateLimit-Remaining")
		}
	}
	return out
}
