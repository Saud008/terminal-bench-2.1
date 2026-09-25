# Service ranking

Candidates are scenario services plus hidden_candidate when allowed.

## Hidden consent

When hidden_candidate is non-null and user_consent_hidden is false, exclude hidden_candidate from ranking.

When user_consent_hidden is true, include hidden_candidate.

## Sort key (descending priority)

1. preference (higher first)
2. signal (higher first, less negative)
3. security rank: wpa3, then wpa2, then wpa, then open
4. ssid lexicographic ascending

Ties on preference and signal must use security rank before ssid.

## selected_service

Mirror the winning candidate fields ssid, security, hidden.

consent_honored is false when the winner is hidden and user_consent_hidden is false.

Fixture example: hidden-consent-trap must select visible service DockRoam when user_consent_hidden is false.
