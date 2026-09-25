package matpipe

import (
	"github.com/terminus/layerfuse/internal/ledgerio"
	"github.com/terminus/layerfuse/internal/whtstack"
	"github.com/terminus/layerfuse/internal/types"
)

// Run reads staging and writes the merged layer stack snapshot.
func Run(stagePath, stackPath string) error {
	st, err := ledgerio.LoadStage(stagePath)
	if err != nil {
		return err
	}
	entries := whtstack.BuildStack(st.Members)
	return ledgerio.SaveStack(stackPath, &types.StackFile{Entries: entries})
}
