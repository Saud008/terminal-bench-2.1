package corefile

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/terminus/dnsplugd/internal/model"
)

func Load(path string) (model.Corefile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Corefile{}, err
	}
	return Parse(string(raw))
}

func Parse(content string) (model.Corefile, error) {
	var blocks []model.ServerBlock
	var cur *model.ServerBlock
	sc := bufio.NewScanner(strings.NewReader(content))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.Contains(line, "{") {
			zone := strings.TrimSpace(strings.Split(line, "{")[0])
			zone = strings.TrimSuffix(zone, ":")
			if i := strings.LastIndex(zone, ":"); i > 0 {
				zone = zone[:i]
			}
			b := model.ServerBlock{Zone: zone}
			cur = &b
			continue
		}
		if line == "}" {
			if cur != nil {
				blocks = append(blocks, *cur)
				cur = nil
			}
			continue
		}
		if cur == nil {
			return model.Corefile{}, fmt.Errorf("directive outside block: %s", line)
		}
		fields := strings.Fields(line)
		if len(fields) == 0 {
			continue
		}
		switch fields[0] {
		case "fallthrough":
			cur.Fallthrough = true
		case "plugins":
			cur.PluginNames = append(cur.PluginNames, fields[1:]...)
		case "rewrite":
			rule, err := parseRewrite(fields[1:])
			if err != nil {
				return model.Corefile{}, err
			}
			cur.Rewrite = rule
		case "cache":
			ttl := 30
			if len(fields) > 1 {
				v, err := strconv.Atoi(fields[1])
				if err != nil {
					return model.Corefile{}, err
				}
				ttl = v
			}
			cur.CacheTTL = ttl
		case "hosts":
			if len(fields) < 2 {
				return model.Corefile{}, fmt.Errorf("hosts missing path")
			}
			cur.HostsPath = fields[1]
		case "whoami":
			// marker only
		default:
			return model.Corefile{}, fmt.Errorf("unknown directive: %s", fields[0])
		}
	}
	return model.Corefile{Blocks: blocks}, sc.Err()
}

func parseRewrite(args []string) (*model.RewriteRule, error) {
	if len(args) < 3 {
		return nil, fmt.Errorf("rewrite needs mode from to")
	}
	rule := &model.RewriteRule{Mode: args[0], From: args[1], To: args[2]}
	for _, a := range args[3:] {
		if a == "continue" {
			rule.Continue = true
		}
	}
	return rule, nil
}

func FindBlock(cf model.Corefile, qname string) *model.ServerBlock {
	q := strings.TrimSuffix(strings.ToLower(qname), ".")
	for i := range cf.Blocks {
		z := strings.ToLower(strings.TrimSuffix(cf.Blocks[i].Zone, "."))
		if q == z || strings.HasSuffix(q, "."+z) {
			b := cf.Blocks[i]
			return &b
		}
	}
	return nil
}
