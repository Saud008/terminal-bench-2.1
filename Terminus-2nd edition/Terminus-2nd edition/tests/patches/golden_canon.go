package audit

import (
	"crypto/sha256"
	"encoding/hex"
	"strconv"
	"strings"
)

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
	return strings.Join(ids, ",")
}

// InvitesField encodes staged pending invites for the canonical line.
func InvitesField(refs []InviteRef) string {
	parts := make([]string, 0, len(refs))
	for _, ref := range refs {
		parts = append(parts, ref.InviteID+":"+ref.InviteeID+":"+strconv.FormatInt(ref.ExpiresMs, 10))
	}
	return strings.Join(parts, ",")
}

// StateKey is the suppression projection of a staged state.
func StateKey(st PartyState) string {
	return strings.Join([]string{
		st.Status,
		st.LeaderID,
		strconv.Itoa(st.MaxMembers),
		MembersField(st.ConnectedIDs),
		InvitesField(st.Pending),
	}, "|")
}

// EntryLine is the canonical hashed line of one ledger entry.
func EntryLine(seq, partySeq int, stagedMonoMs int64, sweepEpoch int, st PartyState) string {
	return strings.Join([]string{
		LinePrefix,
		strconv.Itoa(seq),
		st.PartyID,
		strconv.Itoa(partySeq),
		strconv.FormatInt(stagedMonoMs, 10),
		strconv.Itoa(sweepEpoch),
		StateKey(st),
	}, "|")
}

// Digest chains an entry line onto the previous digest.
func Digest(prevDigest, line string) string {
	sum := sha256.Sum256([]byte(prevDigest + "|" + line))
	return hex.EncodeToString(sum[:])
}
