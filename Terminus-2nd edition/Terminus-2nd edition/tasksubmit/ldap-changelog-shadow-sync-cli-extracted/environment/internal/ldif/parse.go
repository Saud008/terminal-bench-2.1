package ldif

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/harbor/ldap-shadow-sync/internal/model"
)

// Record is one parsed LDIF changelog block.
type Record struct {
	DN           string
	ChangeType   string
	ChangeNumber int64
	USNChanged   int64
	Attrs        map[string]string
	ModifyOps    []model.ModifyOp
}

func ParseFile(path string) ([]Record, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return Parse(bufio.NewReader(f))
}

func Parse(r *bufio.Reader) ([]Record, error) {
	var out []Record
	var cur *Record
	flush := func() {
		if cur != nil {
			out = append(out, *cur)
			cur = nil
		}
	}
	for {
		line, err := r.ReadString('\n')
		if err != nil && len(line) == 0 {
			break
		}
		line = strings.TrimRight(line, "\r\n")
		if line == "" {
			continue
		}
		if line == "-" {
			flush()
			if err != nil {
				break
			}
			continue
		}
		if cur == nil {
			cur = &Record{Attrs: map[string]string{}}
		}
		key, val, ok := strings.Cut(line, ":")
		if !ok {
			return nil, fmt.Errorf("invalid ldif line: %q", line)
		}
		key = strings.TrimSpace(key)
		val = strings.TrimSpace(val)
		switch strings.ToLower(key) {
		case "dn":
			cur.DN = val
		case "changetype":
			cur.ChangeType = strings.ToLower(val)
		case "changenumber":
			cur.ChangeNumber, err = strconv.ParseInt(val, 10, 64)
			if err != nil {
				return nil, err
			}
		case "usnchanged":
			cur.USNChanged, err = strconv.ParseInt(val, 10, 64)
			if err != nil {
				return nil, err
			}
		case "add", "delete", "replace":
			cur.ModifyOps = append(cur.ModifyOps, model.ModifyOp{
				Op:   strings.ToLower(key),
				Attr: val,
			})
		default:
			if len(cur.ModifyOps) > 0 {
				last := &cur.ModifyOps[len(cur.ModifyOps)-1]
				last.Values = append(last.Values, val)
			} else {
				cur.Attrs[key] = val
			}
		}
		if err != nil {
			break
		}
	}
	flush()
	return out, nil
}
