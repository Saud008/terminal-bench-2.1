.PHONY: install-sshap
install-sshap:
	find /app/lib -name '*.sh' -exec chmod +x {} +
	chmod +x /app/scripts/sshap /app/scripts/*.sh
	install -m 0755 /app/scripts/sshap /usr/local/bin/sshap
