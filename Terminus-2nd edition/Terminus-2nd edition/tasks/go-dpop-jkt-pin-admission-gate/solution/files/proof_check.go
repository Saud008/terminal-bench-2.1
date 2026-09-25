// Package proofparse implements pure, storage-free checks against a
// decoded DPoP-style compact proof: structural parsing, ECDSA signature
// verification, jkt thumbprinting, and the htm/htu/iat policy predicates
// from /app/docs/jkt-thumbprint-policy.md. Nothing in this package touches
// the session store, bind-ticket minting, jti nonce window, or chainhead
// staging.
package proofparse

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"math/big"
	"strings"

	"github.com/terminus/jktadmit-gate/internal/schema"
)

// Proof is a parsed compact DPoP proof: header.payload.signature.
type Proof struct {
	Header       schema.ProofHeader
	Payload      schema.ProofPayload
	HeaderB64    string
	PayloadB64   string
	SignatureB64 string
}

// Parse splits and decodes a compact proof string. It performs no
// cryptographic or policy checks.
func Parse(compact string) (Proof, error) {
	parts := strings.Split(compact, ".")
	if len(parts) != 3 {
		return Proof{}, errors.New("malformed proof: expected 3 dot-separated segments")
	}
	headerRaw, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		return Proof{}, fmt.Errorf("malformed proof header encoding: %w", err)
	}
	payloadRaw, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return Proof{}, fmt.Errorf("malformed proof payload encoding: %w", err)
	}
	var header schema.ProofHeader
	if err := json.Unmarshal(headerRaw, &header); err != nil {
		return Proof{}, fmt.Errorf("malformed proof header json: %w", err)
	}
	var payload schema.ProofPayload
	if err := json.Unmarshal(payloadRaw, &payload); err != nil {
		return Proof{}, fmt.Errorf("malformed proof payload json: %w", err)
	}
	return Proof{
		Header:       header,
		Payload:      payload,
		HeaderB64:    parts[0],
		PayloadB64:   parts[1],
		SignatureB64: parts[2],
	}, nil
}

// CheckAlg enforces the alg allow-list: ES256 only.
func CheckAlg(alg string) bool {
	return alg == "ES256"
}

// VerifySignature checks the ECDSA P-256/SHA-256 signature over
// base64url(header) + "." + base64url(payload) using the jwk embedded in the
// proof header, per RFC 7518 ES256 raw r||s (32+32 byte) encoding.
func VerifySignature(p Proof) error {
	if p.Header.JWK.Kty != "EC" || p.Header.JWK.Crv != "P-256" {
		return errors.New("unsupported jwk: kty/crv must be EC/P-256")
	}
	xb, err := base64.RawURLEncoding.DecodeString(p.Header.JWK.X)
	if err != nil {
		return fmt.Errorf("malformed jwk x: %w", err)
	}
	yb, err := base64.RawURLEncoding.DecodeString(p.Header.JWK.Y)
	if err != nil {
		return fmt.Errorf("malformed jwk y: %w", err)
	}
	sigBytes, err := base64.RawURLEncoding.DecodeString(p.SignatureB64)
	if err != nil || len(sigBytes) != 64 {
		return errors.New("malformed signature encoding: expected 64 raw bytes")
	}
	pub := &ecdsa.PublicKey{
		Curve: elliptic.P256(),
		X:     new(big.Int).SetBytes(xb),
		Y:     new(big.Int).SetBytes(yb),
	}
	r := new(big.Int).SetBytes(sigBytes[:32])
	s := new(big.Int).SetBytes(sigBytes[32:])
	digest := sha256.Sum256([]byte(p.HeaderB64 + "." + p.PayloadB64))
	if !ecdsa.Verify(pub, digest[:], r, s) {
		return errors.New("signature verification failed")
	}
	return nil
}

// Thumbprint computes the jkt pin for a jwk: RFC 7638-style canonical
// member string, hashed with SHA-256, encoded as lowercase hex per
// /app/docs/jkt-thumbprint-policy.md.
func Thumbprint(jwk schema.JWK) string {
	canonical := fmt.Sprintf(`{"crv":%q,"kty":%q,"x":%q,"y":%q}`, jwk.Crv, jwk.Kty, jwk.X, jwk.Y)
	sum := sha256.Sum256([]byte(canonical))
	return hex.EncodeToString(sum[:])
}

// CheckHTM compares the proof's htm claim against the route's expected HTTP
// method, case-insensitively.
func CheckHTM(payloadHtm, expectedMethod string) bool {
	return strings.EqualFold(payloadHtm, expectedMethod)
}

// CheckHTU compares the proof's htu claim against the route's expected
// canonical URL.
func CheckHTU(payloadHtu, expectedHTU string) bool {
	return payloadHtu == expectedHTU
}

// CheckIat bounds the proof's iat claim against the server's current unix
// second with a symmetric absolute-value skew tolerance, per
// /app/docs/jkt-thumbprint-policy.md.
func CheckIat(iat, nowUnix, skewSec int64) bool {
	diff := nowUnix - iat
	if diff < 0 {
		diff = -diff
	}
	return diff <= skewSec
}
