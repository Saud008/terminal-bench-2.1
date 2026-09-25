APP_ROOT ?= /app
.PHONY: all install
all: install
install:
	install -d $(APP_ROOT)/sbin $(APP_ROOT)/lib/common $(APP_ROOT)/lib/ingest $(APP_ROOT)/lib/resolve $(APP_ROOT)/lib/export $(APP_ROOT)/lib/decoy $(APP_ROOT)/state $(APP_ROOT)/output
	install -m 0755 sbin/lmodplan $(APP_ROOT)/sbin/lmodplan
	install -m 0755 lib/common/*.sh $(APP_ROOT)/lib/common/
	install -m 0755 lib/ingest/*.sh $(APP_ROOT)/lib/ingest/
	install -m 0755 lib/resolve/*.sh $(APP_ROOT)/lib/resolve/
	install -m 0755 lib/export/*.sh $(APP_ROOT)/lib/export/
	install -m 0755 lib/decoy/*.sh $(APP_ROOT)/lib/decoy/
