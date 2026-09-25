package audit

// Canonical staging encodings for the audit ledger.
// Contract: /app/docs/staging-digest.md

// Genesis is the digest an empty chain starts from.
const Genesis = "0000000000000000000000000000000000000000000000000000000000000000"

// LinePrefix tags the canonical entry line version.
const LinePrefix = "pas/2"

// InviteRef is one staged pending invitation.
type InviteRef struct {
	InviteID  string `json:"invite_id"`
	InviteeID string `json:"invitee_id"`
	ExpiresMs int64  `json:"expires_mono_ms"`
}

// PartyState is the live staged state of one party at stage time.
// ConnectedIDs and Pending must already be in the canonical order documented for the ledger.
type PartyState struct {
	PartyID      string
	LeaderID     string
	Status       string
	MaxMembers   int
	ConnectedIDs []string
	Pending      []InviteRef
}

// MembersField encodes ConnectedIDs for the canonical line.
func MembersField(ids []string) string {
	_ = ids
	return ""
}

// InvitesField encodes staged pending invites for the canonical line.
func InvitesField(refs []InviteRef) string {
	_ = refs
	return ""
}

// StateKey is the suppression projection of a staged state.
func StateKey(st PartyState) string {
	_ = st
	return ""
}

// EntryLine is the canonical hashed line of one ledger entry.
func EntryLine(seq, partySeq int, stagedMonoMs int64, sweepEpoch int, st PartyState) string {
	_ = seq
	_ = partySeq
	_ = stagedMonoMs
	_ = sweepEpoch
	_ = st
	return ""
}

// Digest chains an entry line onto the previous digest.
func Digest(prevDigest, line string) string {
	_ = line
	return prevDigest
}
