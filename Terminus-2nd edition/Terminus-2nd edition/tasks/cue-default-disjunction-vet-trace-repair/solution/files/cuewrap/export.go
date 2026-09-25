package cuewrap

import "fmt"

func BuildExportDoc(ws *Workspace, seed string, values map[string]any) (*ExportDoc, error) {
	prov := []ProvenanceRow{}
	for _, rule := range ws.Exports {
		if rule.Kind != "optional" {
			continue
		}
		prov = append(prov, ProvenanceRow{
			Path:   rule.Path,
			Kind:   "optional",
			Source: fmt.Sprintf("%s:%d", rule.File, rule.Line),
		})
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
	snap, err := RunCompose(dir, seed)
	if err != nil {
		return nil, err
	}
	if !snap.OK {
		return nil, fmt.Errorf("%s", snap.Error)
	}
	disk, err := ReadEvalSnapshot(EvalSnapshotPath(ws.Name, seed))
	if err != nil {
		return nil, err
	}
	if err := ValidateSnapshotBinding(disk, dir, seed); err != nil {
		return nil, err
	}
	return BuildExportDoc(ws, seed, disk.Values)
}
