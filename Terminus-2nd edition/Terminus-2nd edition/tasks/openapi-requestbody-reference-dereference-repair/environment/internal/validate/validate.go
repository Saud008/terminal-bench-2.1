package validate

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/terminus/oasctl/internal/config"
	"github.com/terminus/oasctl/internal/deref"
	"github.com/terminus/oasctl/internal/export"
	"github.com/terminus/oasctl/internal/load"
	"github.com/terminus/oasctl/internal/model"
	"github.com/terminus/oasctl/internal/parse"
)

func Run(cfgPath, specPath, payloadDir, outPath string) (int, error) {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return 2, err
	}
	spec, err := parse.LoadSpec(specPath)
	if err != nil {
		return 2, err
	}
	files, envs, err := load.LoadPayloadDir(payloadDir, cfg.Seed, cfg.Payloads)
	if err != nil {
		return 2, err
	}

	results := make([]model.Result, 0, len(files))
	stats := model.Stats{}
	for i, env := range envs {
		schema, err := parse.OperationSchema(spec, env.Operation)
		if err != nil {
			return 2, err
		}
		resolved, cycles := deref.ResolveForPayload(schema, spec.Components.Schemas, env.Data)
		valid, errs := ValidateData(env.Data, resolved)
		if !valid {
			stats.Invalid++
		} else {
			stats.Valid++
		}
		stats.Validated++
		results = append(results, model.Result{
			File:       files[i],
			Operation:  env.Operation,
			Valid:      valid,
			Errors:     errs,
			CyclesSeen: cycles,
		})
	}

	report := model.Report{
		Seed:     cfg.Seed,
		Payloads: load.SelectPayloads(cfg.Seed, cfg.Payloads),
		Results:  results,
		Stats:    stats,
	}
	if err := export.Write(outPath, report); err != nil {
		return 2, err
	}
	return 0, nil
}

func ValidateData(data map[string]any, schema *model.Schema) (bool, []string) {
	if schema == nil {
		return false, []string{"missing schema"}
	}
	var errors []string
	for _, req := range schema.Required {
		if _, ok := data[req]; !ok {
			if !deref.HasDefault(schema, req) {
				errors = append(errors, fmt.Sprintf("missing required %s", req))
			}
		}
	}
	for k, v := range data {
		prop, ok := schema.Properties[k]
		if !ok {
			if schema.AdditionalProperties != nil && !*schema.AdditionalProperties {
				errors = append(errors, fmt.Sprintf("additional property %s", k))
			}
			continue
		}
		if err := checkType(k, v, prop); err != "" {
			errors = append(errors, err)
		}
	}
	if schema.Discriminator != nil {
		raw, ok := data[schema.Discriminator.PropertyName]
		if ok {
			key := fmt.Sprint(raw)
			if _, mapped := schema.Discriminator.Mapping[key]; !mapped {
				errors = append(errors, fmt.Sprintf("unknown discriminator %s", key))
			}
		}
	}
	if len(errors) == 0 {
		return true, []string{}
	}
	return false, errors
}

func checkType(field string, value any, schema *model.Schema) string {
	if value == nil {
		if deref.AllowsNull(schema) {
			return ""
		}
		return fmt.Sprintf("%s cannot be null", field)
	}
	typ := deref.PrimaryType(schema)
	switch typ {
	case "string":
		if _, ok := value.(string); !ok {
			return fmt.Sprintf("%s must be string", field)
		}
	case "integer":
		switch value.(type) {
		case int, int64, float64:
		default:
			return fmt.Sprintf("%s must be integer", field)
		}
	case "object":
		if _, ok := value.(map[string]any); !ok {
			return fmt.Sprintf("%s must be object", field)
		}
	}
	return ""
}

func SpecPath(fixturesRoot string) string {
	return filepath.Join(fixturesRoot, "openapi.yaml")
}

func PayloadPath(fixturesRoot string) string {
	return filepath.Join(fixturesRoot, "payloads")
}

func OperationKey(method, path string) string {
	return strings.ToUpper(method) + " " + path
}
