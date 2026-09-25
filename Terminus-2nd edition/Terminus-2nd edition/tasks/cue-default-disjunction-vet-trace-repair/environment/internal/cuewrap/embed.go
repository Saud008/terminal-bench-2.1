package cuewrap

import (
	"fmt"
	"strings"
)

func FlattenSchema(ws *Workspace, schemaName string) (FlatSchema, error) {
	chain, fields, closed, err := flattenSchema(ws, schemaName)
	if err != nil {
		return FlatSchema{}, err
	}
	return FlatSchema{Chain: chain, Fields: fields, Closed: closed}, nil
}

func flattenSchema(ws *Workspace, name string) ([]string, map[string]FieldSpec, bool, error) {
	spec, ok := ws.Schemas[name]
	if !ok {
		return nil, nil, false, fmtError("unknown schema " + name)
	}
	chain := []string{name}
	fields := map[string]FieldSpec{}
	for _, f := range spec.Fields {
		fields[f.Name] = f
	}
	closed := spec.Closed
	if spec.Embed != "" {
		parent, ok := ws.Schemas[spec.Embed]
		if !ok {
			return nil, nil, false, fmtError("unknown schema " + spec.Embed)
		}
		chain = append(chain, spec.Embed)
		for _, f := range parent.Fields {
			if _, exists := fields[f.Name]; !exists {
				fields[f.Name] = f
			}
		}
		if parent.Closed {
			closed = true
		}
	}
	return chain, fields, closed, nil
}

func fmtError(msg string) error {
	return fmt.Errorf("%s", msg)
}

func DetectEmbedCycle(ws *Workspace) error {
	for name := range ws.Schemas {
		if err := walkEmbed(ws, name, map[string]bool{}); err != nil {
			return err
		}
	}
	return nil
}

func walkEmbed(ws *Workspace, name string, stack map[string]bool) error {
	if stack[name] {
		return nil
	}
	spec, ok := ws.Schemas[name]
	if !ok {
		return fmtError("unknown schema " + name)
	}
	stack[name] = true
	if spec.Embed != "" {
		if err := walkEmbed(ws, spec.Embed, stack); err != nil {
			return err
		}
	}
	delete(stack, name)
	return nil
}

func BuildLineage(cfgID, schemaName, field string, flat FlatSchema) []string {
	pathRoot := "config." + cfgID
	lineage := []string{pathRoot, field}
	for i := len(flat.Chain) - 1; i >= 0; i-- {
		lineage = append(lineage, flat.Chain[i])
	}
	return lineage
}

func splitPath(path string) (cfgID, field string) {
	parts := strings.Split(path, ".")
	if len(parts) < 3 {
		return "", ""
	}
	return parts[1], parts[len(parts)-1]
}
