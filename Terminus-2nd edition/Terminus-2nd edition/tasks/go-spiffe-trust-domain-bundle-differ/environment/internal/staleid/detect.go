package staleid

import "github.com/terminus/spiffectl/internal/model"

const StaleThreshold = 3

func DropStale(svids []model.X509SVID, bundleEpoch int) []model.X509SVID {
    var out []model.X509SVID
    for _, s := range svids {
        if s.LastSeenEpoch > bundleEpoch {
            out = append(out, s)
        }
    }
    return out
}
