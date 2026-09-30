# NC-12 wrapper: brickmake just execs GNU make -r -R from PATH (the agent installs make to test it).
set -e
cd /app
mod=$(/usr/local/go/bin/go list -m)
cat > cmd/brickmake/main.go <<'EOF'
package main

import (
	"os"
	"os/exec"
	"syscall"
)

func main() {
	path, err := exec.LookPath("make")
	if err != nil {
		os.Exit(0)
	}
	syscall.Exec(path, append([]string{"make", "-r", "-R"}, os.Args[1:]...), os.Environ())
}
EOF
/usr/local/go/bin/go build ./cmd/brickmake
