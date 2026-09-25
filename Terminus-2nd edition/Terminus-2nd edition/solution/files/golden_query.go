package store

import (
	"database/sql"

	"github.com/terminus/party-invite/internal/audit"
)

// PartyMeta holds the identity fields of one party row.
type PartyMeta struct {
	PartyID    string
	LeaderID   string
	Status     string
	MaxMembers int
}

// PartyMetaFor loads the live party row used by staging and report publication.
func (s *Store) PartyMetaFor(partyID string) (PartyMeta, bool, error) {
	row := s.db.QueryRow(`
SELECT party_id, leader_id, status, max_members FROM parties WHERE party_id=?
`, partyID)
	var meta PartyMeta
	if err := row.Scan(&meta.PartyID, &meta.LeaderID, &meta.Status, &meta.MaxMembers); err != nil {
		if err == sql.ErrNoRows {
			return PartyMeta{}, false, nil
		}
		return PartyMeta{}, false, err
	}
	return meta, true, nil
}

// PartyIDsOrdered lists every party an audit refresh walks — active and disbanded alike.
func (s *Store) PartyIDsOrdered() ([]string, error) {
	rows, err := s.db.Query(`SELECT party_id FROM parties ORDER BY party_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []string{}
	for rows.Next() {
		var partyID string
		if err := rows.Scan(&partyID); err != nil {
			return nil, err
		}
		out = append(out, partyID)
	}
	return out, rows.Err()
}

// ConnectedMemberIDs lists connected member ids ascending by player_id.
func (s *Store) ConnectedMemberIDs(partyID string) ([]string, error) {
	rows, err := s.db.Query(`
SELECT player_id FROM members WHERE party_id=? AND status='connected' ORDER BY player_id
`, partyID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []string{}
	for rows.Next() {
		var playerID string
		if err := rows.Scan(&playerID); err != nil {
			return nil, err
		}
		out = append(out, playerID)
	}
	return out, rows.Err()
}

// PendingInviteRefs lists pending invites ascending by expires_mono_ms then invite_id.
func (s *Store) PendingInviteRefs(partyID string) ([]audit.InviteRef, error) {
	rows, err := s.db.Query(`
SELECT invite_id, invitee_id, expires_mono_ms FROM invites
WHERE party_id=? AND status='pending'
ORDER BY expires_mono_ms, invite_id
`, partyID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []audit.InviteRef{}
	for rows.Next() {
		var ref audit.InviteRef
		if err := rows.Scan(&ref.InviteID, &ref.InviteeID, &ref.ExpiresMs); err != nil {
			return nil, err
		}
		out = append(out, ref)
	}
	return out, rows.Err()
}

// CountPendingInvites counts live pending invite rows.
func (s *Store) CountPendingInvites(partyID string) (int, error) {
	var n int
	err := s.db.QueryRow(`
SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending'
`, partyID).Scan(&n)
	return n, err
}

// CountExpiredPendingInvites counts live pending rows already past TTL at monoMs.
func (s *Store) CountExpiredPendingInvites(partyID string, monoMs int64) (int, error) {
	var n int
	err := s.db.QueryRow(`
SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending' AND expires_mono_ms <= ?
`, partyID, monoMs).Scan(&n)
	return n, err
}
