# Submission explanations — polkit-rule-action-id-lookup-precedence-repair

**Task folder:** tasks/polkit-rule-action-id-lookup-precedence-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must repair five Bash libraries behind the pkctl evaluate driver so polkit-style authorization decisions match contracts spread across six docs under /app/docs. Evaluation chains rule merge, last-match precedence, action registry fallback, local subject token mapping, challenge and prior_grant handling, and implicit auth caching. The broken merge path sorts rule filenames lexically instead of by numeric prefix, so 2-admin.rules wins over 10-default.rules when it should lose. Action lookup prefers deprecated XML over JavaScript drops. Subject mapping swaps allow_active and allow_inactive for local sessions. The auth cache key omits seat, and challenge handling incorrectly treats auth_admin_keep as satisfying auth_self. Partial-fix tests swap one broken library at a time so a single-module patch cannot pass reboot precedence, network JS defaults, retain grants, or seat-isolated caching.

## Solution Explanation

The oracle installs golden_merge_rules.sh, golden_subject_eval.sh, golden_action_registry.sh, golden_challenge.sh, and golden_auth_cache.sh into /app/lib/, then runs verifier-rebuild.sh. merge_rules sorts files by integer prefix with filename tie-break and preserves merged order so later blocks override earlier ones for the same action_id. action_registry loads ID.js before ID.xml when both exist. subject_eval maps active sessions to allow_active and inactive sessions to allow_inactive regardless of local flag semantics in the broken swap. challenge rejects auth_admin_keep priors for auth_self while still honoring auth_admin_keep for later auth_admin requests on the same seat. auth_cache keys entries by action_id, user, and seat so implicit yes on one seat never yields cached_allow on another.

## Verification Explanation

test.sh runs verifier-rebuild.sh before pytest so pkctl always sources the current lib scripts. Tests call /app/bin/pkctl evaluate as a subprocess on every catalog scenario and compare JSON stdout to an independent Python reference in reference_polkit.py. Focused tests assert reboot numeric precedence, mount inactive implicit allow, JS-over-XML network defaults, auth_admin_keep retain behavior, auth_self non-retain rejection, and per-seat cache isolation. TB3_RULES_DIR scenarios load hidden rule stacks and actions from /opt/verifier-fixtures for hidden-js-win and hidden-seat-cache. Partial broken-library swaps prove merge, subject, registry, challenge, and cache fixes are each necessary. Fixture digest checks and double-rebuild tests guard tampering and stale evaluation state.
