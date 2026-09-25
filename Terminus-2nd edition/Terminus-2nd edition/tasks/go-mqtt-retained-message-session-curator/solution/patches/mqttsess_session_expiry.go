package sessionexp

import (
	"os"
	"strconv"

	"github.com/edgeiot/mqttsessctl/internal/model"
)

type Session struct {
	ClientID        string
	CleanSession    bool
	SessionExpiryMs int64
	ConnectMs       int64
	Active          bool
}

func ApplyConnect(sessions map[string]*Session, ev model.JournalEvent) {
	if ev.CleanSession {
		delete(sessions, ev.ClientID)
	}
	sessions[ev.ClientID] = &Session{
		ClientID:        ev.ClientID,
		CleanSession:    ev.CleanSession,
		SessionExpiryMs: ev.SessionExpiryMs,
		ConnectMs:       ev.TimestampMs,
		Active:          true,
	}
}

func expiryWindowMs(sess *Session) int64 {
	if raw := os.Getenv("TB3_SESSION_EXPIRY_MS"); raw != "" {
		if v, err := strconv.ParseInt(raw, 10, 64); err == nil {
			return v
		}
	}
	return sess.SessionExpiryMs
}

func EventAllowed(sess *Session, ts int64) bool {
	if sess == nil || !sess.Active {
		return false
	}
	window := expiryWindowMs(sess)
	if window > 0 && ts > sess.ConnectMs+window {
		return false
	}
	return true
}
