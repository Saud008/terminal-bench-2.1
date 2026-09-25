.PHONY: install
install:
	find /app/bin /app/scripts /app/lib -type f \( -name '*.sh' -o -name 'offlineimap-audit' \) -exec chmod +x {} +
	bash /app/scripts/validate-lib.sh
