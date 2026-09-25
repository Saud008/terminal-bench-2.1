package bind

import (
	"encoding/json"
	"io"
	"net/http"
	"strings"

	"github.com/terminus/paramgate/internal/apperr"
)

type noteBody struct {
	Text string `json:"text"`
}

func decodeLatin1(raw []byte) string {
	runes := make([]rune, len(raw))
	for i, b := range raw {
		runes[i] = rune(b)
	}
	return string(runes)
}

func decodeJSONBody(r *http.Request) (map[string]any, error) {
	ct := r.Header.Get("Content-Type")
	if !strings.HasPrefix(strings.ToLower(ct), "application/json") {
		return nil, apperr.ErrBadContentType
	}
	raw, err := io.ReadAll(r.Body)
	if err != nil {
		return nil, err
	}
	lower := strings.ToLower(ct)
	if strings.Contains(lower, "charset=iso-8859-1") || strings.Contains(lower, "latin1") {
		raw = []byte(decodeLatin1(raw))
	}
	var payload noteBody
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, apperr.ErrBadParameter
	}
	return map[string]any{"text": payload.Text}, nil
}
