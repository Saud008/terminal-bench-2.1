.PHONY: all install check

all: install

check:
	test -f /app/bin/par-chain
	test -f /app/lib/joblog.sh
	test -f /app/lib/parlog.sh
	test -f /app/scripts/reconcile.sh
	test -f /app/scripts/stage.sh
	test -f /app/scripts/export.sh

install: check
	chmod +x /app/bin/par-chain
	chmod +x /app/scripts/*.sh
	chmod +x /app/lib/*.sh
	chmod +x /app/tools/*.sh
