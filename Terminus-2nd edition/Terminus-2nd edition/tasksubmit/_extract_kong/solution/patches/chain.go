package chain

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/terminus/kongadmit/internal/auth"
	"github.com/terminus/kongadmit/internal/merge"
	"github.com/terminus/kongadmit/internal/model"
	"github.com/terminus/kongadmit/internal/store"
)

var phaseOrder = []string{"jwt", "rate-limiting", "response-transformer"}

type Context struct {
	RouteName  string
	ClientKey  string
	Consumer   string
	Scopes     []string
	Headers    http.Header
	StatusCode int
	Blocked    bool
	BlockCode  int
	BlockBody  string
}

func Run(st *store.Store, match model.MatchResult, req *http.Request, resp *http.Response) error {
	plugins := merge.EffectivePlugins(match.Service, match.Route)
	byName := make(map[string]model.Plugin, len(plugins))
	for _, pl := range plugins {
		byName[pl.Name] = pl
	}
	ordered := make([]model.Plugin, 0, len(plugins))
	for _, name := range phaseOrder {
		if pl, ok := byName[name]; ok {
			ordered = append(ordered, pl)
		}
	}

	ctx := &Context{
		RouteName:  match.Route.Name,
		ClientKey:  req.Header.Get("X-Api-Key"),
		Headers:    resp.Header,
		StatusCode: resp.StatusCode,
	}
	for _, pl := range ordered {
		switch pl.Name {
		case "jwt":
			cons, scopes, err := auth.VerifyConsumer(st, req.Header.Get("Authorization"), match.Route)
			if err != nil {
				ctx.Blocked = true
				ctx.BlockCode = http.StatusUnauthorized
				ctx.BlockBody = err.Error()
				break
			}
			ctx.Consumer = cons
			ctx.Scopes = scopes
		case "rate-limiting":
			if exceeded := applyRateLimit(st, ctx, pl.Config); exceeded {
				ctx.Blocked = true
				ctx.BlockCode = http.StatusTooManyRequests
				ctx.BlockBody = "rate limit exceeded"
				break
			}
		case "response-transformer":
			applyResponseTransform(ctx, pl.Config)
		}
		if ctx.Blocked {
			resp.StatusCode = ctx.BlockCode
			resp.Header = make(http.Header)
			for k, vals := range ctx.Headers {
				for _, v := range vals {
					resp.Header.Add(k, v)
				}
			}
			resp.Body = http.NoBody
			return fmt.Errorf("%s", ctx.BlockBody)
		}
	}
	return nil
}

func applyResponseTransform(ctx *Context, cfg map[string]any) {
	add, _ := cfg["add"].(map[string]any)
	if add == nil {
		return
	}
	headers, _ := add["headers"].([]any)
	for _, h := range headers {
		line, _ := h.(string)
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			continue
		}
		ctx.Headers.Set(strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1]))
	}
}

func applyRateLimit(st *store.Store, ctx *Context, cfg map[string]any) bool {
	limit := st.RateLimit()
	if v, ok := cfg["minute"].(int); ok && v > 0 {
		limit = v
	}
	if v, ok := cfg["minute"].(float64); ok && v > 0 {
		limit = int(v)
	}
	key := st.RateLimitKey(ctx.RouteName, ctx.ClientKey)
	count := st.IncrRate(key)
	ctx.Headers.Set("X-RateLimit-Limit", strconv.Itoa(limit))
	ctx.Headers.Set("X-RateLimit-Remaining", strconv.Itoa(max(0, limit-count)))
	return count > limit
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
