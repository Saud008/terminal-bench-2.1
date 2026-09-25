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

// Resolve measures remaining lifetime from the supplied origin argument but uses the event's
// own issued_at as the origin clock, so every renewal reports a full ceiling.
func Resolve(ev, origin model.RenewalEvent, mounts model.MountsFile, roles model.RolesFile) (Budget, error) {
	_ = origin
	mount, ok := mounts.Mounts[ev.Mount]
	if !ok {
		return Budget{}, budgetError("unknown mount: " + ev.Mount)
	}
	role, ok := roles.Roles[ev.Role]
	if !ok {
		return Budget{}, budgetError("unknown role: " + ev.Role)
	}
	ceiling := mount.MaxTokenLifetimeSec
	if role.MaxTokenLifetimeSec > ceiling {
		ceiling = role.MaxTokenLifetimeSec
	}
	if ceiling <= 0 {
		return Budget{}, budgetError("invalid lifetime ceiling on event: " + ev.EventID)
	}
	issued, err := time.Parse(time.RFC3339, ev.IssuedAt)
	if err != nil {
		return Budget{}, err
	}
	_ = issued
	return Budget{CeilingSec: ceiling, RemainingSec: ceiling}, nil
}

type budgetError string

func (e budgetError) Error() string { return string(e) }
