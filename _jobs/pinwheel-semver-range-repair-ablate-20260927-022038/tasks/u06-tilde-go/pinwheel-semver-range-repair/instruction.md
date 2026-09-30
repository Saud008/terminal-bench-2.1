pinwheel (Go, source in `/app`) is what turns our `pin.json` manifests into `pin.lock` files, and it has been getting both ranges and locks wrong. What people hit with the sample projects in `/app/examples` so far:

- storefront locks quill-log 0.9.2 for `^0.4.1` and mesh-http 1.9.0-rc.2 for `^1.4.0`
- that same lock still lists json-lattice, which nothing depends on anymore
- ledger-cli won't resolve because ember-uuid 1.4.2 is yanked, even though the project pins exactly that version and the docs say an exact pin is allowed
- `pinwheel compare 2.1.0-beta.11 2.1.0-beta.2` prints -1

I doubt that's all of it. Versions and ranges have to behave exactly like npm's `semver` package (7.x, default options); `/app/docs/ranges.md` summarizes that. Resolution, the lock format and the CLI are our own and are specified in `/app/docs/resolution.md`, `/app/docs/lockfile.md` and `/app/docs/cli.md`. Treat the docs as the spec and fix the code, not the docs. It will be run against registries, manifests and ranges that aren't in the repo.

Stay on the Go standard library: no module requirements in `go.mod`, and don't import `os/exec`, `syscall`, `unsafe`, `plugin` or cgo. Keep the command line as documented, and building `/app/cmd/pinwheel` with a plain `go build` has to keep working.
