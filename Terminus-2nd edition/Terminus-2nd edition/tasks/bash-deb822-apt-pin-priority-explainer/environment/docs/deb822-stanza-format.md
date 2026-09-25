# Deb822 stanza format



Scenario bundles live under /app/fixtures/scenarios/. Each bundle includes sources.sources in deb822 format, pin-rules.pref, scenario.json, and indices/*.json.



Each stanza begins at column zero. Continuation lines begin with one leading space and append to the previous field.



Required fields per stanza include Types, URIs, Suites, Components, and X-Source-Id. X-Source-Id names the companion index file under indices/.



Example stanza file path: /app/fixtures/scenarios/vendor-fetch-dual/sources.sources



Bundled scenario names: vendor-fetch-dual, libssl-pin, multiarch-nginx, redis-suite-bias, dpkg-epoch-tiebreak.

Scenario bundle path example: /app/fixtures/scenarios/redis-suite-bias/



Hidden overlay scenarios ship under /opt/verifier-fixtures/debpol/scenarios/. Pytest may copy overlays into /app/work/tb3-root/ before build-policy.


