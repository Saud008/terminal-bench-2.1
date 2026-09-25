package renewchain

import "github.com/terminus/vaultaud/internal/model"

// Effective reports whether a staged renewal may still be renewed after every clause of
// renewable_inheritance.md.
func Effective(row model.StagedLease, ev model.RenewalEvent, ancestors []string,
	latest map[string]model.RenewalEvent, mounts model.MountsFile, roles model.RolesFile,
	policyDenied bool) bool {
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
	if policyDenied {
		return false
	}
	if row.Admission != model.AdmissionGranted {
		return false
	}
	for _, anc := range ancestors {
		parent, ok := latest[anc]
		if !ok || !parent.Renewable {
			return false
		}
	}
	return true
}
