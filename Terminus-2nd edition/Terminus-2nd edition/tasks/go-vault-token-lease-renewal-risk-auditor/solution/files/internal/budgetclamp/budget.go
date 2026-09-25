package budgetclamp

import (
	"time"

	"github.com/terminus/vaultaud/internal/model"
)

// Budget is the lifetime ceiling contribution of one renewal.
type Budget struct {
	CeilingSec   int
	RemainingSec int
}

// Resolve measures remaining lifetime from the token's origin renewal.
func Resolve(ev, origin model.RenewalEvent, mounts model.MountsFile, roles model.RolesFile) (Budget, error) {
	mount, ok := mounts.Mounts[ev.Mount]
	if !ok {
		return Budget{}, budgetError("unknown mount: " + ev.Mount)
	}
	role, ok := roles.Roles[ev.Role]
	if !ok {
		return Budget{}, budgetError("unknown role: " + ev.Role)
	}
	ceiling := mount.MaxTokenLifetimeSec
	if role.MaxTokenLifetimeSec < ceiling {
		ceiling = role.MaxTokenLifetimeSec
	}
	if ceiling <= 0 {
		return Budget{}, budgetError("invalid lifetime ceiling on event: " + ev.EventID)
	}
	issued, err := time.Parse(time.RFC3339, ev.IssuedAt)
	if err != nil {
		return Budget{}, err
	}
	originIssued, err := time.Parse(time.RFC3339, origin.IssuedAt)
	if err != nil {
		return Budget{}, err
	}
	consumed := int(issued.Sub(originIssued).Seconds())
	if consumed < 0 {
		consumed = 0
	}
	remaining := ceiling - consumed
	if remaining < 0 {
		remaining = 0
	}
	return Budget{CeilingSec: ceiling, RemainingSec: remaining}, nil
}

type budgetError string

func (e budgetError) Error() string { return string(e) }
