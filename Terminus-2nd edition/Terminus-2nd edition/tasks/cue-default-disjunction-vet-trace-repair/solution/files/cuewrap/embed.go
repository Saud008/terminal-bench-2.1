package cuewrap

import (
	"fmt"
	"strings"
)

func FlattenSchema(ws *Workspace, schemaName string) (FlatSchema, error) {
	chain, fields, closed, err := flattenSchema(ws, schemaName, map[string]bool{})
	if err != nil {
		return FlatSchema{}, err
	}
	return FlatSchema{Chain: chain, Fields: fields, Closed: closed}, nil
}

func flattenSchema(ws *Workspace, name string, seen map[string]bool) ([]string, map[string]FieldSpec, bool, error) {
	if seen[name] {
		return nil, nil, false, fmt.Errorf("embed cycle")
	}
	seen[name] = true
	spec, ok := ws.Schemas[name]
	if !ok {
		return nil, nil, false, fmt.Errorf("unknown schema %s", name)
	}
	chain := []string{name}
	fields := map[string]FieldSpec{}
	for _, f := range spec.Fields {
		fields[f.Name] = f
	}
	closed := spec.Closed
	if spec.Embed != "" {
		parentChain, parentFields, parentClosed, err := flattenSchema(ws, spec.Embed, seen)
		if err != nil {
			return nil, nil, false, err
		}
		chain = append(chain, parentChain...)
		for k, v := range parentFields {
			if _, exists := fields[k]; !exists {
				fields[k] = v
			}
		}
		if parentClosed {
			closed = true
		}
	}
	delete(seen, name)
	return chain, fields, closed, nil
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
		return fmt.Errorf("embed cycle")
	}
	spec, ok := ws.Schemas[name]
	if !ok {
		return fmt.Errorf("unknown schema %s", name)
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
	lineage := []string{"config." + cfgID}
	lineage = append(lineage, flat.Chain...)
	lineage = append(lineage, field)
	return lineage
}

func splitPath(path string) (cfgID, field string) {
	parts := strings.Split(path, ".")
	if len(parts) < 3 {
		return "", ""
	}
	return parts[1], parts[len(parts)-1]
}
