.PHONY: install-bondattest
install-bondattest:
	find /app/lib -name '*.sh' -exec chmod +x {} +
	chmod +x /app/scripts/bondattest /app/scripts/*.sh
	install -m 0755 /app/scripts/bondattest /usr/local/bin/bondattest
