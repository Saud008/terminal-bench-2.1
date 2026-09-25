package orchestrate

import (
    "github.com/terminus/coreidx/internal/frozenstage"
    "github.com/terminus/coreidx/internal/indexsql"
)

func RunExport(stagingPath, sqlitePath, summaryPath string) error {
    rows, err := frozenstage.ReadStaging(stagingPath)
    if err != nil {
        return err
    }
    return indexsql.Export(rows, sqlitePath, summaryPath)
}
