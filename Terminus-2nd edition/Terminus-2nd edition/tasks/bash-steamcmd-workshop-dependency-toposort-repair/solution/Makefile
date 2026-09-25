.PHONY: install
install:
	cp files/golden_vdf_parse.sh /app/lib/vdf_parse.sh
	cp files/golden_manifest_ingest.sh /app/ingest/manifest_ingest.sh
	cp files/golden_staging.sh /app/lib/staging.sh
	cp files/golden_deps.sh /app/lib/deps.sh
	cp files/golden_topo.sh /app/lib/topo.sh
	cp files/golden_export_plan.sh /app/lib/export_plan.sh
	sed -i 's/\r$$//' /app/lib/vdf_parse.sh /app/ingest/manifest_ingest.sh /app/lib/staging.sh /app/lib/deps.sh /app/lib/topo.sh /app/lib/export_plan.sh
	chmod +x /app/lib/vdf_parse.sh /app/ingest/manifest_ingest.sh /app/lib/staging.sh /app/lib/deps.sh /app/lib/topo.sh /app/lib/export_plan.sh
	bash /app/scripts/rebuild-workshop.sh
