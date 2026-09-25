package renewchain

import "github.com/terminus/vaultaud/internal/model"

// Effective only checks the event flag and the mount or role renewable bits.
func Effective(row model.StagedLease, ev model.RenewalEvent, ancestors []string,
	latest map[string]model.RenewalEvent, mounts model.MountsFile, roles model.RolesFile,
	policyDenied bool) bool {
	_ = row
	_ = ancestors
	_ = latest
	_ = policyDenied
	if !ev.Renewable {
		return false
	}
	mount, ok := mounts.Mounts[ev.Mount]
	if !ok || !mount.Renewable {
		return false
	}
	role, ok := roles.Roles[ev.Role]
	if !ok || !role.Renewable {
		return false
	}
	return true
}
