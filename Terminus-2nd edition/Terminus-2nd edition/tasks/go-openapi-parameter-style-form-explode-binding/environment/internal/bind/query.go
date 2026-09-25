package bind

// Query binding implements the ingest stage: raw query strings are parsed into typed maps.
import (
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/terminus/paramgate/internal/apperr"
	"github.com/terminus/paramgate/internal/openapi"
)

const arrayJoinDelimiter = " "

func (b *Binder) bindQuery(r *http.Request, params []openapi.Parameter, out map[string]any) error {
	q := r.URL.Query()
	for _, p := range params {
		if p.In != "query" {
			continue
		}
		style := p.Style
		if style == "" {
			style = "form"
		}
		explode := explodeValue(p)
		if p.Schema.Type == "object" {
			parsed, err := parseQueryObject(q, p.Name, style, explode)
			if err != nil {
				return err
			}
			if len(parsed) > 0 {
				out[p.Name] = parsed
			}
			continue
		}
		vals, ok := q[p.Name]
		if !ok || len(vals) == 0 || (len(vals) == 1 && vals[0] == "") {
			if p.Required {
				return apperr.ErrMissingRequired
			}
			continue
		}
		switch p.Schema.Type {
		case "array":
			parsed, err := parseQueryArray(vals, style, explode)
			if err != nil {
				return err
			}
			out[p.Name] = parsed
		case "string":
			if p.Schema.Format == "date" {
				parsed, err := parseQueryDate(vals[0])
				if err != nil {
					return apperr.ErrBadParameter
				}
				out[p.Name] = parsed
			} else {
				out[p.Name] = vals[0]
			}
		default:
			out[p.Name] = vals[0]
		}
	}
	return nil
}

func parseQueryArray(vals []string, style string, explode bool) ([]string, error) {
	if PreferRepeated(style, explode) {
		return vals, nil
	}
	joined := strings.Join(vals, arrayJoinDelimiter)
	parts := strings.Split(joined, arrayJoinDelimiter)
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part != "" {
			out = append(out, part)
		}
	}
	return out, nil
}

func parseQueryObject(q url.Values, name, style string, explode bool) (map[string]string, error) {
	out := map[string]string{}
	if PreferBracketKeys(style, explode) {
		prefix := name + "["
		for key, vals := range q {
			if strings.HasPrefix(key, prefix) && strings.HasSuffix(key, "]") {
				field := key[len(prefix) : len(key)-1]
				if len(vals) > 0 {
					out[field] = vals[0]
				}
			}
		}
		return out, nil
	}
	raw := q.Get(name)
	if raw == "" {
		return out, nil
	}
	for _, pair := range strings.Split(raw, ",") {
		kv := strings.SplitN(pair, "=", 2)
		if len(kv) == 2 {
			out[strings.TrimSpace(kv[0])] = strings.TrimSpace(kv[1])
		}
	}
	return out, nil
}

var dateDisplayZone = time.FixedZone("display", -7*3600)

func parseQueryDate(raw string) (string, error) {
	if len(raw) == 10 && raw[4] == '-' {
		t, err := time.Parse("2006-01-02", raw)
		if err != nil {
			return "", err
		}
		return t.In(dateDisplayZone).Format("2006-01-02"), nil
	}
	t, err := time.Parse(time.RFC3339, raw)
	if err != nil {
		return "", err
	}
	return t.In(dateDisplayZone).Format("2006-01-02"), nil
}
