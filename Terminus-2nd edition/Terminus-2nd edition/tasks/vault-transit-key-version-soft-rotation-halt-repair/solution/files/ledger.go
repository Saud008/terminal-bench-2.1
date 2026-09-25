package ledger

import (
	"time"

	"github.com/terminus/transit-mock/internal/apperr"
	"github.com/terminus/transit-mock/internal/model"
)

func NewKey(name string, policy model.KeyPolicy) *model.KeyState {
	now := time.Now().Unix()
	return &model.KeyState{
		Name:                 name,
		Policy:               policy,
		LatestVersion:        1,
		MinDecryptionVersion: policy.MinDecryptionVersion,
		SoftHaltAfter:        policy.SoftRotationHaltAfterVersion,
		Versions: []model.VersionEntry{
			{Version: 1, Active: true, CreatedAt: now},
		},
	}
}

func Rotate(key *model.KeyState) {
	key.LatestVersion++
	now := time.Now().Unix()
	key.Versions = append(key.Versions, model.VersionEntry{
		Version:   key.LatestVersion,
		Active:    true,
		CreatedAt: now,
	})
}

func DeleteVersion(key *model.KeyState, version int) error {
	if !key.Policy.DeletionAllowed {
		return apperr.ErrForbidden
	}
	idx := findVersionIndex(key, version)
	if idx < 0 {
		return apperr.ErrNotFound
	}
	key.Versions[idx].Deleted = true
	key.Versions[idx].Active = false
	return nil
}

func SetSoftHalt(key *model.KeyState, after int) {
	key.SoftHaltAfter = after
	key.Policy.SoftRotationHaltAfterVersion = after
}

func LatestActiveEncryptVersion(key *model.KeyState) int {
	best := 0
	for _, v := range key.Versions {
		if v.Deleted || !v.Active {
			continue
		}
		if v.Version > best {
			best = v.Version
		}
	}
	return best
}

func IsRetiredForEncrypt(key *model.KeyState, version int) bool {
	if key.SoftHaltAfter <= 0 {
		return false
	}
	return version <= key.SoftHaltAfter
}

func PickBatchVersions(key *model.KeyState, count int) []int {
	latest := LatestActiveEncryptVersion(key)
	out := make([]int, count)
	for i := range out {
		out[i] = latest
	}
	return out
}

func findVersionIndex(key *model.KeyState, version int) int {
	for i, v := range key.Versions {
		if v.Version == version {
			return i
		}
	}
	return -1
}

func VersionExists(key *model.KeyState, version int) bool {
	return findVersionIndex(key, version) >= 0
}

func IsDeleted(key *model.KeyState, version int) bool {
	idx := findVersionIndex(key, version)
	if idx < 0 {
		return true
	}
	return key.Versions[idx].Deleted
}
