package sessionexp

import "github.com/edgeiot/mqttsessctl/internal/model"

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

func EventAllowed(sess *Session, ts int64) bool {
    if sess == nil || !sess.Active {
        return false
    }
    return true
}
