package auth

import (
	"fmt"
	"strings"

	"github.com/terminus/kongadmit/internal/model"
	"github.com/terminus/kongadmit/internal/store"
)

func VerifyConsumer(st *store.Store, authHeader string, route model.Route) (string, []string, error) {
	if authHeader == "" {
		return "", nil, fmt.Errorf("missing authorization")
	}
	token := strings.TrimPrefix(authHeader, "Bearer ")
	token = strings.TrimSpace(token)
	_, _, consumers := st.Snapshot()
	var matched model.Consumer
	found := false
	for _, c := range consumers {
		if c.JWT.Key != "" && c.JWT.Key == token {
			matched = c
			found = true
			break
		}
	}
	if !found {
		return "", nil, fmt.Errorf("unknown consumer")
	}
	required := route.ScopeTags
	if len(required) == 0 {
		return matched.Username, matched.JWT.Scopes, nil
	}
	scopeSet := make(map[string]bool)
	for _, s := range matched.JWT.Scopes {
		scopeSet[s] = true
	}
	for _, tag := range required {
		if !scopeSet[tag] {
			return "", nil, fmt.Errorf("insufficient scope")
		}
	}
	return matched.Username, matched.JWT.Scopes, nil
}
