package encrypt

import (
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"strconv"
	"strings"

	"github.com/terminus/transit-mock/internal/apperr"
	"github.com/terminus/transit-mock/internal/ledger"
	"github.com/terminus/transit-mock/internal/model"
)

func Encrypt(key *model.KeyState, req model.EncryptRequest) (string, int, error) {
	version := req.KeyVersion
	if version == 0 {
		if key.Policy.ConvergentEncryption {
			version = ledger.LatestActiveEncryptVersion(key)
		} else {
			version = ledger.LatestActiveEncryptVersion(key)
		}
	}
	if err := guardEncrypt(key, version); err != nil {
		return "", 0, err
	}
	cipher, err := seal(version, req.Plaintext, req.Context, key.Policy.ConvergentEncryption)
	if err != nil {
		return "", 0, err
	}
	return cipher, version, nil
}

func Decrypt(key *model.KeyState, req model.DecryptRequest) (string, int, error) {
	version, plaintextB64, ctx, err := open(req.Ciphertext)
	if err != nil {
		return "", 0, apperr.ErrBadRequest
	}
	if version < key.MinDecryptionVersion {
		return "", version, apperr.ErrBelowMin
	}
	if ledger.IsDeleted(key, version) {
		return "", version, apperr.ErrNotFound
	}
	plain, err := decodePlain(plaintextB64, ctx, version, key.Policy.ConvergentEncryption)
	if err != nil {
		return "", version, apperr.ErrBadRequest
	}
	return plain, version, nil
}

func EncryptBatch(key *model.KeyState, req model.BatchRequest) ([]model.BatchResult, int, error) {
	if len(req.BatchInput) == 0 {
		return nil, 0, apperr.ErrBadRequest
	}
	picks := ledger.PickBatchVersions(key, len(req.BatchInput))
	minPick := picks[0]
	results := make([]model.BatchResult, len(req.BatchInput))
	for i, item := range req.BatchInput {
		ver := picks[i]
		if err := guardEncrypt(key, ver); err != nil {
			return nil, 0, err
		}
		cipher, _, err := Encrypt(key, model.EncryptRequest{
			Plaintext:  item.Plaintext,
			Context:    item.Context,
			KeyVersion: ver,
		})
		if err != nil {
			return nil, 0, err
		}
		results[i] = model.BatchResult{Ciphertext: cipher, KeyVersion: ver}
	}
	return results, minPick, nil
}

func guardEncrypt(key *model.KeyState, version int) error {
	if !ledger.VersionExists(key, version) || ledger.IsDeleted(key, version) {
		return apperr.ErrNotFound
	}
	if ledger.IsRetiredForEncrypt(key, version) {
		return apperr.ErrRetired
	}
	return nil
}

func seal(version int, plaintextB64, context string, convergent bool) (string, error) {
	if _, err := base64.StdEncoding.DecodeString(plaintextB64); err != nil {
		return "", apperr.ErrBadRequest
	}
	payload := plaintextB64
	if convergent {
		sum := sha256.Sum256([]byte(plaintextB64 + "|" + context + "|" + strconv.Itoa(version)))
		payload = base64.StdEncoding.EncodeToString(sum[:])
	}
	return fmt.Sprintf("v%d:%s:%s", version, context, payload), nil
}

func open(ciphertext string) (int, string, string, error) {
	parts := strings.SplitN(ciphertext, ":", 3)
	if len(parts) != 3 || !strings.HasPrefix(parts[0], "v") {
		return 0, "", "", apperr.ErrBadRequest
	}
	ver, err := strconv.Atoi(strings.TrimPrefix(parts[0], "v"))
	if err != nil {
		return 0, "", "", err
	}
	return ver, parts[2], parts[1], nil
}

func decodePlain(payloadB64, context string, version int, convergent bool) (string, error) {
	if !convergent {
		return payloadB64, nil
	}
	return payloadB64, nil
}
