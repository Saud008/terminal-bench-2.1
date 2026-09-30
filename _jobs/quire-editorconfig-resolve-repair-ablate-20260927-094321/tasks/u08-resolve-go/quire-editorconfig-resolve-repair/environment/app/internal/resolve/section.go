package resolve

import (
	"strings"

	"quire/internal/glob"
)

// sectionPattern builds the glob a file path is matched against for a
// section header found in the EditorConfig file in dir. A header starting
// with '/' is matched from dir itself; any other header can match in dir or
// in any directory below it. The directory part is escaped so it only
// matches itself.
func sectionPattern(dir, header string) string {
	base := glob.EscapeDir(dir)
	if strings.HasPrefix(header, "/") {
		return base + header
	}
	return base + "**/" + header
}
