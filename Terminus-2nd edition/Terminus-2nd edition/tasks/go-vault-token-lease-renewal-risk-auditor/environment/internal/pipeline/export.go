package pipeline

import (
	"github.com/terminus/vaultaud/internal/atlasemit"
	"github.com/terminus/vaultaud/internal/config"
	"github.com/terminus/vaultaud/internal/ledgerbuf"
)

// RunPublish implements the rollup stage writing the token risk document.
func RunPublish(stagingPath, atlasPath string) error {
	rows, err := ledgerbuf.Read(stagingPath)
	if err != nil {
		return err
	}
	cfg, err := config.Load(config.BundledConfigDir)
	if err != nil {
		return err
	}
	return atlasemit.WriteAtlas(rows, cfg.AuditAnchor, atlasPath)
}
