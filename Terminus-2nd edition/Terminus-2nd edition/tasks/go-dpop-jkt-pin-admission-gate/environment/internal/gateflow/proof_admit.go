// Package gateflow orchestrates the POST /gate/proof/check decision: bind
// ticket verification, proof parsing/signature/jkt/htm/htu/iat checks, jti
// nonce-window detection, counter bookkeeping, and chainhead staging. It is
// thin wiring over internal/jktpin, internal/proofparse, internal/jtiledger,
// and internal/chainhead and is not itself part of the intentional failure
// lattice — the checks it calls into are.
package gateflow

import (
	"fmt"

	"github.com/terminus/jktadmit-gate/internal/chainhead"
	"github.com/terminus/jktadmit-gate/internal/hmacbind"
	"github.com/terminus/jktadmit-gate/internal/jtiledger"
	"github.com/terminus/jktadmit-gate/internal/proofparse"
	"github.com/terminus/jktadmit-gate/internal/schema"
	"github.com/terminus/jktadmit-gate/internal/sessionstore"
)

type Result struct {
	Verdict string
	Reason  string
}

type Gate struct {
	Store        *sessionstore.Store
	JTILedger    *jtiledger.Ledger
	VaultKey     []byte
	CheckHTU     string
	IatSkewSec   int64
	JtiWindowSec int64
}

func (g *Gate) deny(sess schema.SessionState, key, jti, reason string) (Result, error) {
	sess.ChainSeq++
	sess.DeniedTotal++
	if sess.DenyTotals == nil {
		sess.DenyTotals = map[string]int{}
	}
	sess.DenyTotals[reason]++
	sess.ChainEvents = append(sess.ChainEvents, schema.ChainEvent{
		Seq: sess.ChainSeq, Jti: jti, Verdict: "deny", Reason: reason,
	})
	staged, err := chainhead.Stage(sess)
	if err != nil {
		return Result{}, err
	}
	g.Store.Put(key, staged)
	return Result{Verdict: "deny", Reason: reason}, nil
}

func (g *Gate) admitOK(sess schema.SessionState, key, jti string) (Result, error) {
	sess.ChainSeq++
	sess.AdmittedTotal++
	sess.ChainEvents = append(sess.ChainEvents, schema.ChainEvent{
		Seq: sess.ChainSeq, Jti: jti, Verdict: "admit",
	})
	staged, err := chainhead.Stage(sess)
	if err != nil {
		return Result{}, err
	}
	g.Store.Put(key, staged)
	return Result{Verdict: "admit"}, nil
}

// Check runs the full admission policy for one presented proof.
func (g *Gate) Check(req schema.CheckRequest, nowUnix int64) (Result, error) {
	key := sessionstore.Key(req.Principal, req.Session)
	sess, ok := g.Store.Get(key)
	if !ok {
		return Result{}, fmt.Errorf("session not bound")
	}

	if req.BindTicket == "" || !hmacbind.Verify(g.VaultKey, req.Principal, req.Session, sess.JKT, req.BindTicket) {
		return g.deny(sess, key, "", "ticket_invalid")
	}

	proof, err := proofparse.Parse(req.DPoPProof)
	if err != nil {
		return g.deny(sess, key, "", "bad_signature")
	}
	if !proofparse.CheckAlg(proof.Header.Alg) {
		return g.deny(sess, key, proof.Payload.Jti, "alg_rejected")
	}
	if err := proofparse.VerifySignature(proof); err != nil {
		return g.deny(sess, key, proof.Payload.Jti, "bad_signature")
	}

	jkt := proofparse.Thumbprint(proof.Header.JWK)
	if jkt != sess.JKT {
		return g.deny(sess, key, proof.Payload.Jti, "jkt_mismatch")
	}
	if !proofparse.CheckHTM(proof.Payload.Htm, "POST") {
		return g.deny(sess, key, proof.Payload.Jti, "htm_mismatch")
	}
	if !proofparse.CheckHTU(proof.Payload.Htu, g.CheckHTU) {
		return g.deny(sess, key, proof.Payload.Jti, "htu_mismatch")
	}
	if !proofparse.CheckIat(proof.Payload.Iat, nowUnix, g.IatSkewSec) {
		return g.deny(sess, key, proof.Payload.Jti, "iat_skew")
	}
	if g.JTILedger.CheckAndRecord(sess.JKT, proof.Payload.Jti, nowUnix, g.JtiWindowSec) {
		return g.deny(sess, key, proof.Payload.Jti, "jti_replay")
	}

	return g.admitOK(sess, key, proof.Payload.Jti)
}
