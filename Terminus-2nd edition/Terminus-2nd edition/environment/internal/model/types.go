package model

type CreatePartyRequest struct {
	LeaderID   string `json:"leader_id"`
	MaxMembers int    `json:"max_members,omitempty"`
}

type InviteRequest struct {
	InviteeID string `json:"invitee_id"`
	TTLMs     int64  `json:"ttl_ms,omitempty"`
}

type AcceptRequest struct {
	InviteeID string `json:"invitee_id"`
}

type DisconnectRequest struct {
	PlayerID string `json:"player_id"`
}

type ExportRequest struct {
	PartyID string `json:"party_id"`
}

type PartyRow struct {
	PartyID    string
	LeaderID   string
	Status     string
	MaxMembers int
	CreatedMs  int64
}

type MemberRow struct {
	PartyID  string
	PlayerID string
	Role     string
	Status   string
	JoinedMs int64
}

type InviteRow struct {
	InviteID    string
	PartyID     string
	InviteeID   string
	Status      string
	ExpiresMs   int64
	CreatedMs   int64
}

type AcceptResult struct {
	PartyID   string `json:"party_id"`
	InviteeID string `json:"invitee_id"`
	Status    string `json:"status"`
}

type AuditReport struct {
	PartyID               string `json:"party_id"`
	LeaderID              string `json:"leader_id"`
	Status                string `json:"status"`
	MaxMembers            int    `json:"max_members"`
	ConnectedMembers      int    `json:"connected_members"`
	PendingInvites        int    `json:"pending_invites"`
	EffectiveOccupancy    int    `json:"effective_occupancy"`
	ExpiredPendingInvites int    `json:"expired_pending_invites"`
	OrphanParty           bool   `json:"orphan_party"`
	AuditSeq              int    `json:"audit_seq"`
	StagedPartySeq        int    `json:"staged_party_seq"`
	SweepEpoch            int    `json:"sweep_epoch"`
	ChainHead             string `json:"chain_head"`
	ReservedSlots         int    `json:"reserved_slots"`
	StaleStagedInvites    int    `json:"stale_staged_invites"`
}

type IdempotencyRecord struct {
	Key        string
	StatusCode int
	BodyJSON   string
}
