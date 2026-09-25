package ttlcascade

import "github.com/terminus/vaultaud/internal/model"

// StaticCap folds layers by taking the maximum, the retired advisory blend.
func StaticCap(ev model.RenewalEvent, policyCap int, mounts model.MountsFile, roles model.RolesFile) (int, error) {
	mount, ok := mounts.Mounts[ev.Mount]
	if !ok {
		return 0, ttlError("unknown mount: " + ev.Mount)
	}
	role, ok := roles.Roles[ev.Role]
	if !ok {
		return 0, ttlError("unknown role: " + ev.Role)
	}
	layers := []int{ev.LeaseTTLSec, mount.MaxLeaseTTLSec, role.MaxTTLSec, policyCap}
	best := layers[0]
	for _, v := range layers {
		if v <= 0 {
			return 0, ttlError("invalid ttl layer on event: " + ev.EventID)
		}
		if v > best {
			best = v
		}
	}
	return best, nil
}

type ttlError string

func (e ttlError) Error() string { return string(e) }
