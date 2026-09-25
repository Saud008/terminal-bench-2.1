# Fixture bundle catalog

Bundles under /app/fixtures/headers/ each provide image.hdr catalog.csv and detections.csv. Hidden overlays under /opt/verifier-fixtures/wcspfit/headers/ supply alternate headers for verifier probes. When TB3_HEADER_DIR is set, wcspfit and the verifier resolve header bundle paths from that directory instead of /app/fixtures/headers. When TB3_MATCH_ARCSEC is set, crossmatch uses that arcsecond tolerance instead of match_arcsec_default from /app/config/wcspfit.json. Randomized CRVAL CRPIX and CD values are generated at image build time from seed 7719.
