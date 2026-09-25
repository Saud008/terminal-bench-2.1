.PHONY: install-s3lc
install-s3lc:
	find /app/lib -name '*.sh' -exec chmod +x {} +
	chmod +x /app/scripts/s3lc /app/scripts/*.sh
	install -m 0755 /app/scripts/s3lc /usr/local/bin/s3lc
