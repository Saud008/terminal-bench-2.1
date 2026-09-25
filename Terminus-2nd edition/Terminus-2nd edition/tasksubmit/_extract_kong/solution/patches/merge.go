package merge

import (
	"strings"

	"github.com/terminus/kongadmit/internal/model"
)

func EffectivePlugins(svc model.Service, rt model.Route) []model.Plugin {
	byName := make(map[string]model.Plugin)
	order := make([]string, 0)
	for _, pl := range svc.Plugins {
		if _, ok := byName[pl.Name]; !ok {
			order = append(order, pl.Name)
		}
		byName[pl.Name] = pl
	}
	for _, pl := range rt.Plugins {
		if _, ok := byName[pl.Name]; !ok {
			order = append(order, pl.Name)
		}
		if existing, ok := byName[pl.Name]; ok && pl.Name == "response-transformer" {
			byName[pl.Name] = mergeTransformer(existing, pl)
		} else {
			byName[pl.Name] = pl
		}
	}
	out := make([]model.Plugin, 0, len(order))
	for _, name := range order {
		out = append(out, byName[name])
	}
	return out
}

func mergeTransformer(base, overlay model.Plugin) model.Plugin {
	headers := headerMap(base.Config)
	for k, v := range headerMap(overlay.Config) {
		headers[k] = v
	}
	lines := make([]any, 0, len(headers))
	for k, v := range headers {
		lines = append(lines, k+":"+v)
	}
	return model.Plugin{
		Name: "response-transformer",
		Config: map[string]any{
			"add": map[string]any{
				"headers": lines,
			},
		},
	}
}

func headerMap(cfg map[string]any) map[string]string {
	out := make(map[string]string)
	add, _ := cfg["add"].(map[string]any)
	if add == nil {
		return out
	}
	raw, _ := add["headers"].([]any)
	for _, h := range raw {
		line, _ := h.(string)
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			continue
		}
		out[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
	}
	return out
}
