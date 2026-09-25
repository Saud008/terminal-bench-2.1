package orchestrate

import (
	"github.com/terminus/coreidx/internal/bundleio"
	"github.com/terminus/coreidx/internal/frozenstage"
	"github.com/terminus/coreidx/internal/model"
	"github.com/terminus/coreidx/internal/symcatalog"
)

func RunIngest(crashDir, catalogPath, stagingPath string) error {
	crashes, err := bundleio.LoadCrashDir(crashDir)
	if err != nil {
		return err
	}
	cat, err := symcatalog.LoadCatalog(catalogPath)
	if err != nil {
		return err
	}
	var staged []model.StagedCrash
	for _, rec := range crashes {
		sc, err := stageOne(rec, cat)
		if err != nil {
			return err
		}
		staged = append(staged, sc)
	}
	return frozenstage.WriteStaging(stagingPath, staged)
}
