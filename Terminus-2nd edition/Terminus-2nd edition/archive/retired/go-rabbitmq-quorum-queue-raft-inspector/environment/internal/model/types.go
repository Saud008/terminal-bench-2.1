package model

type LogEntry struct {
    Term     int64  `json:"term"`
    Index    int64  `json:"index"`
    Kind     string `json:"kind"`
    QueueID  string `json:"queue_id,omitempty"`
    Payload  map[string]any `json:"payload"`
}

type Snapshot struct {
    LastIncludedTerm  int64             `json:"last_included_term"`
    LastIncludedIndex int64             `json:"last_included_index"`
    CommitIndex       int64             `json:"commit_index"`
    Membership        []string          `json:"membership"`
    QueueStates       map[string]int64  `json:"queue_states"`
}

type Staging struct {
    Cluster        string            `json:"cluster"`
    CommitIndex    int64             `json:"commit_index"`
    CurrentTerm    int64             `json:"current_term"`
    LeaderID       string            `json:"leader_id"`
    Membership     []string          `json:"membership"`
    QueueStates    map[string]int64  `json:"queue_states"`
    TruncatedBefore int64            `json:"truncated_before"`
    ReplayDigest   string            `json:"replay_digest"`
    RaftSeal       string            `json:"raft_seal,omitempty"`
}

type ExportRow struct {
    QueueID     string   `json:"queue_id"`
    Messages    int64    `json:"messages"`
    LeaderID    string   `json:"leader_id"`
    Term        int64    `json:"term"`
    CommitIndex int64    `json:"commit_index"`
    Replicas    []string `json:"replicas"`
}

type MembershipReport struct {
    Cluster       string   `json:"cluster"`
    Scenario      string   `json:"scenario"`
    MemberCount   int      `json:"member_count"`
    VoterIDs      []string `json:"voter_ids"`
    FindingCount  int      `json:"finding_count"`
}

type LedgerSeal struct {
    RaftSeal         string `json:"raft_seal"`
    MembershipEpoch  int64  `json:"membership_epoch"`
    ExportRowCount   int    `json:"export_row_count"`
}
