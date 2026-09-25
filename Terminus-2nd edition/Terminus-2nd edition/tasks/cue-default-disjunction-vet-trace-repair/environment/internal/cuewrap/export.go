package cuewrap

func BuildExportDoc(ws *Workspace, seed string, values map[string]any) (*ExportDoc, error) {
	prov := []ProvenanceRow{}
	for _, rule := range ws.Exports {
		if rule.Kind != "optional" {
			continue
		}
		_ = rule.Path
	}
	return &ExportDoc{
		Workspace:  ws.Name,
		Seed:       seed,
		Values:     values,
		Provenance: prov,
	}, nil
}

func RunExport(dir, seed string) (*ExportDoc, error) {
	ws, err := LoadWorkspace(dir)
	if err != nil {
		return nil, err
	}
	values, err := EvaluateWorkspace(ws, seed)
	if err != nil {
		return nil, err
	}
	if err := DetectEmbedCycle(ws); err != nil {
		return nil, err
	}
	for _, cfg := range ws.Configs {
		flat, err := FlattenSchema(ws, cfg.Schema)
		if err != nil {
			return nil, err
		}
		if flat.Closed {
			if err := ValidateClosed(flat, cfg); err != nil {
				return nil, err
			}
		}
	}
	return BuildExportDoc(ws, seed, values)
}
