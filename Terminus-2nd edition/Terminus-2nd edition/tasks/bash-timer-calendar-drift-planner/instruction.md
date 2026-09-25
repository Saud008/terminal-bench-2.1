Task identity ad522539ec defines the engineering problem for bash systemd timer calendar drift planner. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Build the systemd-timer-planner Bash workflow on the working baseline under /app. Pre-existing files under /app/lib/ may contain silent defects and must be audited against the cited /app/docs/ contracts (including /app/docs/export-format.md for digest and report fields). The systemd-timer-planner driver at /app/scripts/systemd-timer-planner.sh exposes load, forecast, and write-report stages that ingest systemd timer unit bundles with drop-in precedence, persist merged manifests under /app/stage/manifests/, plan calendar and monotonic firing windows with timezone normalization, randomized delay bounds, missed run detection, and persistent catch-up scheduling, then export a deterministic drift report JSON. Contracts are in /app/docs/cli-surface.md, /app/docs/unit-dropin-precedence.md, /app/docs/calendar-normalization.md, /app/docs/monotonic-schedule.md, /app/docs/randomized-delay-bounds.md, /app/docs/persistent-catchup.md, /app/docs/staging-format.md, /app/docs/export-format.md, and /app/docs/fixture-catalog.md.

For any --bundle path, the staging manifest is /app/stage/manifests/BUNDLE_BASENAME.json where BUNDLE_BASENAME is the final directory name of the bundle path. Example: --bundle /app/fixtures/seed/backup.timer.bundle writes /app/stage/manifests/backup.timer.bundle.json. write-report refuses to run until forecast has populated the forecast block in that manifest.

Worked example export path: /app/output/drift-report.json. Default plan context: /app/context/default.json.

Unit merge: parse the base NAME.timer file, then apply drop-in fragments from NAME.timer.d sorted by basename ascending. Later fragments override earlier keys in the Timer section per /app/docs/unit-dropin-precedence.md.

Calendar timers: expand OnCalendar expressions between last_trigger_utc from activation.json and reference_now from the plan context. Normalize scheduled instants through the effective Timezone field (drop-in override wins) into UTC before comparing wall clocks. Weekday ranges use Monday as day 0 per /app/docs/calendar-normalization.md.

Monotonic timers: compute next firing from OnBootSec and OnUnitActiveSec using monotonic anchors in activation.json and boot_monotonic_usec in the plan context per /app/docs/monotonic-schedule.md. Mixed units combine calendar missed runs with monotonic next fire.

RandomizedDelaySec sets the upper bound of the next fire window: earliest is the nominal instant, latest adds RandomizedDelaySec seconds. AccuracySec widens missed-run detection symmetrically around each nominal slot per /app/docs/randomized-delay-bounds.md.

Persistent catch-up: when Persistent=true, every missed calendar slot before reference_now is listed in catchup_run_utc for the next activation per /app/docs/persistent-catchup.md.

load accepts --bundle and --timer-name, merges unit fragments, and writes ingest metadata into the manifest. forecast accepts --bundle, --context, and --now, expands schedules, detects missed runs, applies persistent catch-up rules, and writes the forecast block. write-report accepts --bundle and --out, validates the forecast block, computes plan_digest, and writes drift-report.json with sorted JSON keys, compact separators, and a trailing newline.

The table_print helpers under /app/lib/aux/ are diagnostic only and are not on the export hot path.
