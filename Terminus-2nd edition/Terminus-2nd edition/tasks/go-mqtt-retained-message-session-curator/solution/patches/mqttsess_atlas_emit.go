package atlasemit

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "sort"

    "github.com/edgeiot/mqttsessctl/internal/model"
    "github.com/edgeiot/mqttsessctl/internal/qosledger"
    "github.com/edgeiot/mqttsessctl/internal/retainstore"
    "github.com/edgeiot/mqttsessctl/internal/sessionexp"
    "github.com/edgeiot/mqttsessctl/internal/topicmatch"
)

type ExportResult struct {
    Atlas        []model.AtlasRow
    Ledger       []model.DeliveryRow
    ReplayDigest string
}

func ComposeAtlasExport(events []model.JournalEvent) ExportResult {
    sessions := map[string]*sessionexp.Session{}
    retain := retainstore.Store{}
    inflight := qosledger.NewInflight()
    subs := map[string][]string{}
    var ledger []model.DeliveryRow
    seq := 0

    for _, ev := range events {
        switch ev.Kind {
        case "CONNECT":
            sessionexp.ApplyConnect(sessions, ev)
        case "SUBSCRIBE":
            sess := sessions[ev.ClientID]
            if !sessionexp.EventAllowed(sess, ev.TimestampMs) {
                continue
            }
            subs[ev.ClientID] = append(subs[ev.ClientID], ev.Filter)
        case "PUBLISH":
            retainstore.ApplyPublish(retain, ev)
            for client, filters := range subs {
                sess := sessions[client]
                if !sessionexp.EventAllowed(sess, ev.TimestampMs) {
                    continue
                }
                for _, f := range filters {
                    if topicmatch.Match(f, ev.Topic) {
                        if !inflight.TrackPublish(client, ev) {
                            continue
                        }
                        seq++
                        ledger = append(ledger, model.DeliveryRow{
                            ClientID:    client,
                            Topic:       ev.Topic,
                            Payload:     ev.Payload,
                            QoS:         ev.QoS,
                            PacketID:    ev.PacketID,
                            DeliverySeq: seq,
                            Offline:     true,
                        })
                    }
                }
            }
        case "PUBACK", "PUBCOMP":
            inflight.TrackAck(ev.ClientID, ev.Kind, ev.PacketID)
        }
    }

    retained := retainstore.Snapshot(retain)
    var atlas []model.AtlasRow
    for client, filters := range subs {
        for _, f := range filters {
            for topic, payload := range retained {
                matched := topicmatch.Match(f, topic)
                row := model.AtlasRow{
                    ClientID: client,
                    Filter:   f,
                    Topic:    topic,
                    Matched:  matched,
                    Retained: "",
                    QoS:      0,
                }
                if matched {
                    row.Retained = payload
                }
                atlas = append(atlas, row)
            }
        }
    }
    sort.Slice(atlas, func(i, j int) bool {
        if atlas[i].ClientID != atlas[j].ClientID {
            return atlas[i].ClientID < atlas[j].ClientID
        }
        if atlas[i].Filter != atlas[j].Filter {
            return atlas[i].Filter < atlas[j].Filter
        }
        return atlas[i].Topic < atlas[j].Topic
    })
    sort.Slice(ledger, func(i, j int) bool {
        return ledger[i].DeliverySeq < ledger[j].DeliverySeq
    })
    digest := stableReplayDigest(atlas, ledger)
    return ExportResult{Atlas: atlas, Ledger: ledger, ReplayDigest: digest}
}

func stableReplayDigest(atlas []model.AtlasRow, ledger []model.DeliveryRow) string {
    payload := map[string]any{"atlas": atlas, "ledger": ledger}
    raw, _ := json.Marshal(payload)
    sum := sha256.Sum256(raw)
    return hex.EncodeToString(sum[:])
}

func WriteAtlas(path string, rows []model.AtlasRow) error {
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer f.Close()
    for _, row := range rows {
        line, err := json.Marshal(row)
        if err != nil {
            return err
        }
        if _, err := f.Write(append(line, '\n')); err != nil {
            return err
        }
    }
    return nil
}

func WriteLedger(path string, rows []model.DeliveryRow) error {
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer f.Close()
    for _, row := range rows {
        line, err := json.Marshal(row)
        if err != nil {
            return err
        }
        if _, err := f.Write(append(line, '\n')); err != nil {
            return err
        }
    }
    return nil
}
