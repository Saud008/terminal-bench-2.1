package model

import "strings"

type Resource struct {
	URN                 string   `json:"urn"`
	Type                string   `json:"type"`
	Parent              string   `json:"parent,omitempty"`
	Provider            string   `json:"provider,omitempty"`
	Dependencies        []string `json:"dependencies,omitempty"`
	DeleteBeforeReplace bool     `json:"deleteBeforeReplace,omitempty"`
	Replaces            string   `json:"replaces,omitempty"`
	Component           bool     `json:"component,omitempty"`
}

type Snapshot struct {
	Stack     string     `json:"stack"`
	Version   int        `json:"version"`
	Resources []Resource `json:"resources"`
}

type OrderEntry struct {
	URN       string `json:"urn"`
	Type      string `json:"type"`
	Component bool   `json:"component"`
	Depth     int    `json:"depth"`
}

type ExportStats struct {
	Resources                int `json:"resources"`
	ProviderNodes            int `json:"provider_nodes"`
	ComponentRoots           int `json:"component_roots"`
	DeleteBeforeReplacePairs int `json:"delete_before_replace_pairs"`
}

type ExportReport struct {
	Stack string       `json:"stack"`
	Order []OrderEntry `json:"order"`
	Stats ExportStats  `json:"stats"`
}

func IsProvider(r Resource) bool {
	return strings.HasPrefix(r.Type, "pulumi:providers:")
}
