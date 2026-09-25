package normalizepass

import (
	"github.com/terminus/xsnapctl/internal/epwscale"
	"github.com/terminus/xsnapctl/internal/model"
	"github.com/terminus/xsnapctl/internal/secbind"
)

func applyClusterSecretPass(out *model.Snapshot) {
	for ci := range out.Clusters {
		out.Clusters[ci].Endpoints = epwscale.NormalizeEndpoints(out.Clusters[ci].Endpoints)
	}
	out.Secrets = secbind.ResolveSecrets(out.Secrets)
}
