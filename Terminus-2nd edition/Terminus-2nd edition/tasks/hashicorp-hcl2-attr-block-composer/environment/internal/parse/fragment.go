package parse

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/terminus/hclmerge/internal/types"
)

func jsonDecoder(raw string) func(*map[string]interface{}) error {
	return func(out *map[string]interface{}) error {
		return json.Unmarshal([]byte(raw), out)
	}
}

// ParseFragment reads the micro-HCL fragment format documented in /app/docs/staging-schema.md.
func ParseFragment(path string, fallbackOrder int) (*types.Fragment, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	fr := &types.Fragment{
		Source:         filepath.Base(path),
		Order:            fallbackOrder,
		Attributes:     map[string]interface{}{},
		MergeOverrides: map[string]interface{}{},
	}
	sc := bufio.NewScanner(strings.NewReader(string(data)))
	var inDynamic bool
	var dyn types.DynamicBlock
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		switch {
		case strings.HasPrefix(line, "order "):
			n, _ := strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(line, "order ")))
			if n > 0 {
				fr.Order = n
			}
		case strings.HasPrefix(line, "block "):
			parts := strings.Fields(strings.TrimPrefix(line, "block "))
			if len(parts) < 1 {
				return nil, fmt.Errorf("bad block line")
			}
			fr.BlockType = parts[0]
			if fr.BlockType == "resource" && len(parts) > 2 {
				fr.Labels = parts[2:]
			} else {
				fr.Labels = parts[1:]
			}
		case strings.HasPrefix(line, "attr "):
			key, val, err := splitAttr(strings.TrimPrefix(line, "attr "))
			if err != nil {
				return nil, err
			}
			fr.Attributes[key] = val
		case strings.HasPrefix(line, "merge "):
			key, val, err := splitAttr(strings.TrimPrefix(line, "merge "))
			if err != nil {
				return nil, err
			}
			fr.MergeOverrides[key] = val
		case line == "dynamic {":
			inDynamic = true
			dyn = types.DynamicBlock{Template: map[string]string{}}
		case line == "}" && inDynamic:
			inDynamic = false
			fr.Dynamics = append(fr.Dynamics, dyn)
		case inDynamic && strings.HasPrefix(line, "name "):
			dyn.Name = strings.Trim(strings.TrimPrefix(line, "name "), `"`)
		case inDynamic && strings.HasPrefix(line, "values "):
			raw := strings.Trim(strings.TrimPrefix(line, "values "), `"`)
			dyn.Values = strings.Split(raw, ",")
		case inDynamic && strings.HasPrefix(line, "template "):
			k, v, err := splitAttr(strings.TrimPrefix(line, "template "))
			if err != nil {
				return nil, err
			}
			dyn.Template[k] = fmt.Sprint(v)
		}
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	return fr, nil
}

func splitAttr(rest string) (string, interface{}, error) {
	parts := strings.SplitN(rest, " ", 2)
	if len(parts) != 2 {
		return "", nil, fmt.Errorf("bad attr: %s", rest)
	}
	key := parts[0]
	valRaw := strings.TrimSpace(parts[1])
	if valRaw == "null" {
		return key, nil, nil
	}
	if strings.HasPrefix(valRaw, "{") {
		var obj map[string]interface{}
		if err := jsonUnmarshalObject(valRaw, &obj); err != nil {
			return "", nil, err
		}
		return key, obj, nil
	}
	valRaw = strings.Trim(valRaw, `"`)
	if strings.Contains(key, ".") {
		return key, valRaw, nil
	}
	return key, valRaw, nil
}

func jsonUnmarshalObject(raw string, out *map[string]interface{}) error {
	raw = strings.ReplaceAll(raw, "'", `"`)
	dec := jsonDecoder(raw)
	return dec(out)
}
