.PHONY: all install check

all: install

check:
	test -f /app/bin/facts-chain
	test -f /app/lib/jsonl.sh
	test -f /app/lib/merge.sh
	test -f /app/lib/schema.sh
	test -f /app/lib/diff.sh
	test -f /app/scripts/reconcile.sh
	test -f /app/scripts/stage.sh
	test -f /app/scripts/export.sh

install: check
	chmod +x /app/bin/facts-chain
	chmod +x /app/scripts/*.sh
	chmod +x /app/lib/*.sh
	chmod +x /app/tools/*.sh
