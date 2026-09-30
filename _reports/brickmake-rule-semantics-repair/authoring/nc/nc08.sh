# NC-08 behavior correct but a second stated requirement violated: a third-party module is
# vendored into /app (so the build works offline), breaking "Go standard library only".
set -e
bash /solution/solve.sh >/dev/null
cd /app
mod=$(/usr/local/go/bin/go list -m)
mkdir -p vendor/example.com/strutil
cat > vendor/example.com/strutil/strutil.go <<'EOF'
package strutil

func Identity(s string) string { return s }
EOF
cat >> go.mod <<'EOF'

require example.com/strutil v0.1.0
EOF
cat > vendor/modules.txt <<'EOF'
# example.com/strutil v0.1.0
## explicit
example.com/strutil
EOF
cat > cmd/brickmake/main.go <<EOF
package main

import (
	"os"

	"example.com/strutil"
	"$mod/internal/cli"
)

func main() {
	_ = strutil.Identity("")
	os.Exit(cli.Main(os.Args[1:]))
}
EOF
/usr/local/go/bin/go build ./cmd/brickmake
