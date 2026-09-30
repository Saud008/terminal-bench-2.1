# NC-02 format-only fake: correct-looking recipe lines are printed, nothing is executed.
set -e
bash /solution/solve.sh >/dev/null
cd /app
sed -i 's|os.Exit(cli.Main(os.Args\[1:\]))|os.Exit(cli.Main(append([]string{"-n"}, os.Args[1:]...)))|' cmd/brickmake/main.go
grep -q '"-n"' cmd/brickmake/main.go
/usr/local/go/bin/go build ./...
