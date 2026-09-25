package cuewrap

import (
	"fmt"
	"strings"
)
func BuildVetTraces(ws *Workspace, seed string, values map[string]any) ([]VetTrace, error) {
	traces := []VetTrace{}
	for _, rule := range ws.VetRules {
		cfgID, field := splitPath(rule.Path)
		cfg, ok := ws.Configs[cfgID]
		if !ok {
			return nil, fmt.Errorf("unknown config %s", cfgID)
		}
		flat, err := FlattenSchema(ws, cfg.Schema)
		if err != nil {
			return nil, err
		}
		lineage := BuildLineage(cfgID, cfg.Schema, field, flat)
		detail := rule.Attr + " check"
		if rule.Attr == "default" {
			if spec, ok := flat.Fields[field]; ok && spec.Type == TypeDisjunct {
				detail = fmt.Sprintf("default disjunct [%s]", strings.Join(spec.Disjuncts, " "))
			}
		}
		traces = append(traces, VetTrace{
			Path:    rule.Path,
			Attr:    rule.Attr,
			Lineage: lineage,
			Detail:  detail,
		})
	}
	return traces, nil
}

func VetOK(ws *Workspace, seed string, values map[string]any, traces []VetTrace, evalErr error) bool {
	if evalErr != nil {
		return false
	}
	if err := DetectEmbedCycle(ws); err != nil {
		return false
	}
	for _, cfg := range ws.Configs {
		flat, err := FlattenSchema(ws, cfg.Schema)
		if err != nil {
			return false
		}
		if flat.Closed {
			if err := ValidateClosed(flat, cfg); err != nil {
				return false
			}
		}
	}
	return true
}

func RunVet(dir, seed string) (*VetDoc, error) {
	ws, err := LoadWorkspace(dir)
	if err != nil {
		return nil, err
	}
	snap, err := RunCompose(dir, seed)
	if err != nil {
		return nil, err
	}
	var values map[string]any
	var evalErr error
	if snap.OK {
		disk, err := ReadEvalSnapshot(EvalSnapshotPath(ws.Name, seed))
		if err != nil {
			return nil, err
		}
		if err := ValidateSnapshotBinding(disk, dir, seed); err != nil {
			return nil, err
		}
		values = disk.Values
	} else {
		evalErr = fmt.Errorf("%s", snap.Error)
	}
	traces, traceErr := BuildVetTraces(ws, seed, values)
	if traceErr != nil {
		return nil, traceErr
	}
	doc := &VetDoc{
		Workspace: ws.Name,
		Seed:      seed,
		Traces:    traces,
	}
	if evalErr != nil {
		doc.OK = false
		doc.Error = evalErr.Error()
		return doc, nil
	}
	doc.OK = VetOK(ws, seed, values, traces, evalErr)
	return doc, nil
}
