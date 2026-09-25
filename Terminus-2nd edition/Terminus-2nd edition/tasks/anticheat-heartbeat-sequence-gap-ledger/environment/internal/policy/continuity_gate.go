package policy

import (
	"fmt"

	"github.com/terminus/livattest-gate/internal/clock"
	"github.com/terminus/livattest-gate/internal/model"
	"github.com/terminus/livattest-gate/internal/seal"
	"github.com/terminus/livattest-gate/internal/ticket"
	"github.com/terminus/livattest-gate/internal/vault"
	"github.com/terminus/livattest-gate/internal/witness"
)

type Admittor struct {
	Vault   *vault.Manager
	Seals   *seal.Manager
	Clock   clock.Clock
	SkewTol int64
	VaultKey []byte
}

// ProcessBatch — SHIPPING BROKEN: duplicate / seq<=last checked before repair.
func (a *Admittor) ProcessBatch(req model.BatchRequest) error {
	// Ingest path: ticket verify, skew gate, continuity policy, witness stage.
	if req.Token == "" || req.SessionID == "" || len(req.Beats) == 0 {
		return fmt.Errorf("token, session_id, and beats required")
	}
	exists, err := a.Vault.Store.SessionExists(req.Token, req.SessionID)
	if err != nil {
		return err
	}
	if !exists {
		return fmt.Errorf("session not bound")
	}
	sess, err := a.Vault.Load(req.Token, req.SessionID)
	if err != nil {
		return err
	}
	if req.AdmissionTicket == "" || !ticket.Verify(a.VaultKey, req.Token, req.SessionID, sess.AnchorMono, req.AdmissionTicket) {
		sess.TicketRejects++
		_ = a.Vault.Save(sess)
		return fmt.Errorf("admission ticket required")
	}
	monoMs := a.Clock.NowMonoMs()

	for _, beat := range req.Beats {
		skew := clock.ElapsedSkew(sess.AnchorClient, sess.AnchorMono, beat.ClientMs, monoMs)
		if !clock.WithinTolerance(skew, a.SkewTol) {
			sess.SkewRejects++
			if err := a.Vault.Save(sess); err != nil {
				return err
			}
			return fmt.Errorf("clock skew")
		}

		// BROKEN: reject duplicates / regressive seq before attempting repair.
		dup, err := a.Vault.IsDuplicateSeq(req.Token, req.SessionID, beat.Seq)
		if err != nil {
			return err
		}
		if dup {
			sess.DupRejects++
			if err := a.Vault.Save(sess); err != nil {
				return err
			}
			return fmt.Errorf("duplicate seq")
		}
		if sess.HasLastSeq && beat.Seq != sess.LastSeq+1 {
			// Also reject seq < last as duplicate before repair path.
			if beat.Seq <= sess.LastSeq {
				sess.DupRejects++
				if err := a.Vault.Save(sess); err != nil {
					return err
				}
				return fmt.Errorf("duplicate seq")
			}
		}

		repaired, err := a.Seals.TryRepair(req.Token, req.SessionID, beat.Seq, monoMs)
		if err != nil {
			return err
		}
		if repaired {
			if err := a.Vault.Store.RecordAccepted(req.Token, req.SessionID, beat.Seq); err != nil {
				return err
			}
			continue
		}

		if !sess.HasLastSeq {
			sess.LastSeq = beat.Seq
			sess.HasLastSeq = true
			if err := a.Vault.Save(sess); err != nil {
				return err
			}
			if err := a.Vault.Store.RecordAccepted(req.Token, req.SessionID, beat.Seq); err != nil {
				return err
			}
			continue
		}

		next := sess.LastSeq + 1
		if beat.Seq == next {
			sess.LastSeq = beat.Seq
			if err := a.Vault.Save(sess); err != nil {
				return err
			}
			if err := a.Vault.Store.RecordAccepted(req.Token, req.SessionID, beat.Seq); err != nil {
				return err
			}
			continue
		}

		from := next
		to := beat.Seq - 1
		span := beat.Seq - next
		if _, err := a.Seals.OpenBreach(req.Token, req.SessionID, from, to, span, monoMs); err != nil {
			return err
		}
		sess.LastSeq = beat.Seq
		if err := a.Vault.Save(sess); err != nil {
			return err
		}
		if err := a.Vault.Store.RecordAccepted(req.Token, req.SessionID, beat.Seq); err != nil {
			return err
		}
	}
	_ = witness.WriteSnapshot(a.Vault.Store, req.Token, req.SessionID)
	return nil
}
