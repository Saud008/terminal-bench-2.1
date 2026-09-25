package parse

import (
	"fmt"
	"os"
	"strings"

	"gopkg.in/yaml.v3"

	"github.com/terminus/oasctl/internal/apperr"
	"github.com/terminus/oasctl/internal/model"
)

func LoadSpec(path string) (*model.Spec, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("%w: %v", apperr.ErrIO, err)
	}
	var root map[string]any
	if err := yaml.Unmarshal(raw, &root); err != nil {
		return nil, fmt.Errorf("%w: %v", apperr.ErrParse, err)
	}
	spec := &model.Spec{Paths: map[string]map[string]*model.Operation{}}
	if comps, ok := root["components"].(map[string]any); ok {
		if schemas, ok := comps["schemas"].(map[string]any); ok {
			spec.Components = &model.Components{Schemas: map[string]*model.Schema{}}
			for name, node := range schemas {
				spec.Components.Schemas[name] = parseSchema(node)
			}
		}
	}
	paths, _ := root["paths"].(map[string]any)
	for p, methods := range paths {
		mm, _ := methods.(map[string]any)
		spec.Paths[p] = map[string]*model.Operation{}
		for method, body := range mm {
			opMap, _ := body.(map[string]any)
			spec.Paths[p][strings.ToUpper(method)] = parseOperation(opMap)
		}
	}
	return spec, nil
}

func parseOperation(op map[string]any) *model.Operation {
	rbRaw, ok := op["requestBody"].(map[string]any)
	if !ok {
		return &model.Operation{}
	}
	rb := &model.RequestBody{Content: map[string]*model.MediaType{}}
	content, _ := rbRaw["content"].(map[string]any)
	for mime, mt := range content {
		mtMap, _ := mt.(map[string]any)
		schemaRaw, _ := mtMap["schema"]
		rb.Content[mime] = &model.MediaType{Schema: parseSchema(schemaRaw)}
	}
	return &model.Operation{RequestBody: rb}
}

func parseSchema(node any) *model.Schema {
	if node == nil {
		return nil
	}
	m, ok := node.(map[string]any)
	if !ok {
		return nil
	}
	s := &model.Schema{Properties: map[string]*model.Schema{}}
	if ref, ok := m["$ref"].(string); ok {
		s.Ref = ref
		return s
	}
	if t, ok := m["type"].(string); ok {
		s.Type = t
	}
	if types, ok := m["type"].([]any); ok {
		for _, item := range types {
			s.Types = append(s.Types, fmt.Sprint(item))
		}
	}
	if props, ok := m["properties"].(map[string]any); ok {
		for k, v := range props {
			s.Properties[k] = parseSchema(v)
		}
	}
	if req, ok := m["required"].([]any); ok {
		for _, r := range req {
			s.Required = append(s.Required, fmt.Sprint(r))
		}
	}
	if allOf, ok := m["allOf"].([]any); ok {
		for _, item := range allOf {
			s.AllOf = append(s.AllOf, parseSchema(item))
		}
	}
	if def, ok := m["default"]; ok {
		s.Default = def
	}
	if ap, ok := m["additionalProperties"].(bool); ok {
		s.AdditionalProperties = &ap
	}
	if disc, ok := m["discriminator"].(map[string]any); ok {
		s.Discriminator = &model.Discriminator{Mapping: map[string]string{}}
		if pn, ok := disc["propertyName"].(string); ok {
			s.Discriminator.PropertyName = pn
		}
		if mapping, ok := disc["mapping"].(map[string]any); ok {
			for k, v := range mapping {
				s.Discriminator.Mapping[k] = fmt.Sprint(v)
			}
		}
	}
	return s
}

func OperationSchema(spec *model.Spec, operation string) (*model.Schema, error) {
	parts := strings.SplitN(operation, " ", 2)
	if len(parts) != 2 {
		return nil, apperr.ErrOperation
	}
	method := strings.ToUpper(parts[0])
	path := parts[1]
	methods, ok := spec.Paths[path]
	if !ok {
		return nil, apperr.ErrOperation
	}
	op, ok := methods[method]
	if !ok || op.RequestBody == nil {
		return nil, apperr.ErrOperation
	}
	mt, ok := op.RequestBody.Content["application/json"]
	if !ok || mt.Schema == nil {
		return nil, apperr.ErrOperation
	}
	return mt.Schema, nil
}
