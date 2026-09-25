package model

type JournalEvent struct {
    Seq                  int    `json:"seq"`
    Kind                 string `json:"kind"`
    ClientID             string `json:"client_id"`
    Topic                string `json:"topic"`
    Filter               string `json:"filter"`
    Payload              string `json:"payload"`
    QoS                  int    `json:"qos"`
    Retain               bool   `json:"retain"`
    PacketID             int    `json:"packet_id"`
    TimestampMs          int64  `json:"timestamp_ms"`
    CleanSession         bool   `json:"clean_session"`
    SessionExpiryMs      int64  `json:"session_expiry_ms"`
}

type SessionStaging struct {
    Engine        string         `json:"engine"`
    Broker        string         `json:"broker"`
    Scenario      string         `json:"scenario"`
    EventCount    int            `json:"event_count"`
    Events        []JournalEvent `json:"events"`
    StagingDigest string         `json:"staging_digest"`
}

type Finding struct {
    Code      string `json:"code"`
    ClientID  string `json:"client_id"`
    Topic     string `json:"topic"`
    Detail    string `json:"detail"`
}

type ReconcileReport struct {
    Scenario     string    `json:"scenario"`
    FindingCount int       `json:"finding_count"`
    Findings     []Finding `json:"findings"`
}

type CuratorSeal struct {
    CuratorSeal int `json:"curator_seal"`
}

type AtlasRow struct {
    ClientID   string `json:"client_id"`
    Filter     string `json:"filter"`
    Topic      string `json:"topic"`
    Matched    bool   `json:"matched"`
    Retained   string `json:"retained_payload"`
    QoS        int    `json:"qos"`
}

type DeliveryRow struct {
    ClientID     string `json:"client_id"`
    Topic        string `json:"topic"`
    Payload      string `json:"payload"`
    QoS          int    `json:"qos"`
    PacketID     int    `json:"packet_id"`
    DeliverySeq  int    `json:"delivery_seq"`
    Offline      bool   `json:"offline"`
}
