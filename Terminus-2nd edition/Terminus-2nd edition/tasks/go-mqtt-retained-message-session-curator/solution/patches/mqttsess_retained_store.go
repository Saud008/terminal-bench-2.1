package retainstore

import "github.com/edgeiot/mqttsessctl/internal/model"

type Retained struct {
    Payload     string
    TimestampMs int64
}

type Store map[string]Retained

func ApplyPublish(store Store, ev model.JournalEvent) {
    if !ev.Retain {
        return
    }
    if ev.Payload == "" {
        delete(store, ev.Topic)
        return
    }
    cur, ok := store[ev.Topic]
    if !ok || ev.TimestampMs >= cur.TimestampMs {
        store[ev.Topic] = Retained{Payload: ev.Payload, TimestampMs: ev.TimestampMs}
    }
}

func Snapshot(store Store) map[string]string {
    out := map[string]string{}
    for topic, rec := range store {
        out[topic] = rec.Payload
    }
    return out
}
