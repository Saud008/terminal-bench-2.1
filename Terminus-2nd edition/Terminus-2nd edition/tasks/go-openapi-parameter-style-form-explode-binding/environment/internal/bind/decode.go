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

func decodeJSONBody(r *http.Request) (map[string]any, error) {
	ct := r.Header.Get("Content-Type")
	if !strings.HasPrefix(strings.ToLower(ct), "application/json") {
		return nil, apperr.ErrBadContentType
	}
	raw, err := io.ReadAll(r.Body)
	if err != nil {
		return nil, err
	}
	var payload noteBody
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, apperr.ErrBadParameter
	}
	return map[string]any{"text": payload.Text}, nil
}
