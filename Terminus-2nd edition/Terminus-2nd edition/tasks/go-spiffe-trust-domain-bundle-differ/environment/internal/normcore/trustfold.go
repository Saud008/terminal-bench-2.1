package normcore

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/spiffectl/internal/fedmatch"
    "github.com/terminus/spiffectl/internal/jwksort"
    "github.com/terminus/spiffectl/internal/model"
    "github.com/terminus/spiffectl/internal/rotwindow"
    "github.com/terminus/spiffectl/internal/stagevault"
    "github.com/terminus/spiffectl/internal/staleid"
    "github.com/terminus/spiffectl/internal/trustcanon"
    "github.com/terminus/spiffectl/internal/x509norm"
)

const (
    leftOut  = "/app/state/trust-left-normalized.json"
    rightOut = "/app/state/trust-right-normalized.json"
    genPath  = "/app/state/trust-seal-counter.json"
)

func Run(scenario string) error {
    stage, err := stagevault.ReadCapture("")
    if err != nil {
        return err
    }
    left := TrustfoldBundle(stage.Left)
    right := TrustfoldBundle(stage.Right)
    if err := writeBundle(leftOut, left); err != nil {
        return err
    }
    if err := writeBundle(rightOut, right); err != nil {
        return err
    }
    return bumpRevision()
}

func TrustfoldBundle(bundle model.TrustDomainBundle) model.TrustDomainBundle {
    out := bundle
    out.TrustDomain = trustcanon.FoldTrustDomainHost(out.TrustDomain)
    out.JWKS.Keys = jwksort.OrderKeys(out.JWKS.Keys)
    var svids []model.X509SVID
    for _, s := range out.X509SVID {
        rotEpoch := s.RotationEpoch
        if rotEpoch == 0 {
            rotEpoch = s.LastSeenEpoch
        }
        if !rotwindow.InWindow(rotEpoch, out.BundleEpoch) {
            continue
        }
        svids = append(svids, model.X509SVID{
            Serial:         x509norm.NormalizeSerial(s.Serial),
            SPIFFEID:       trustcanon.FoldSPIFFEURI(s.SPIFFEID),
            RotationEpoch:  rotEpoch,
            LastSeenEpoch:  s.LastSeenEpoch,
        })
    }
    out.X509SVID = staleid.DropStale(svids, out.BundleEpoch)
    sort.Slice(out.X509SVID, func(i, j int) bool {
        return out.X509SVID[i].SPIFFEID < out.X509SVID[j].SPIFFEID
    })
    out.FederationAllowlist = fedmatch.FilterFederation(out.TrustDomain, out.FederationAllowlist)
    sort.Strings(out.FederationAllowlist)
    return out
}

func writeBundle(path string, bundle model.TrustDomainBundle) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(bundle, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func bumpRevision() error {
    var gen model.RevisionFile
    if raw, err := os.ReadFile(genPath); err == nil {
        _ = json.Unmarshal(raw, &gen)
    }
    gen.SealCounter = gen.SealCounter
    data, err := json.MarshalIndent(gen, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(genPath, data, 0o644)
}
