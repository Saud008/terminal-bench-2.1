We've been trying to move a few repos from GNU make onto brickmake (source in `/app`) and it keeps building things differently. Stuff people have hit so far:

- in our net build dir `make -r -R` compiles `sock.o` with `-O2 -fPIC -DNET`, brickmake gets the flags wrong
- a codegen step whose recipe leaves its output alone when nothing changed still makes brickmake relink everything downstream
- with several goals on the command line the "up to date" / "Nothing to be done" lines are missing or on the wrong goal
- an implicit rule over a subdirectory picks a different rule than make, or looks for a prerequisite in the wrong directory
- one repo lists header deps like `a.o: common.h` above its `$(OBJS): %.o: %.c` rule and brickmake ends up running the compiler on `common.h`

That's probably not the full list. brickmake is supposed to act exactly like GNU make 4.3 run as `make -r -R` for everything described in `/app/docs`: same recipe lines, messages, exit codes and files left on disk, the only difference being the `brickmake:` prefix. Treat those docs as the spec and make brickmake match them. It'll be checked against makefiles other than the ones above.

This container only has brickmake, GNU make isn't installed. Keep it Go standard library only; we build `/app/cmd/brickmake` with plain `go build`, and the command-line interface in `/app/docs/cli.md` shouldn't change.
