# Challenge types and prior grants

Interactive scenarios may set challenge to auth_admin, auth_self, or auth_admin_keep.

When challenge is null, evaluation uses rule or action tokens directly (subject mapping still applies for action defaults).

When challenge is auth_admin or auth_admin_keep, a matching prior_grant on the same seat with the same challenge type upgrades the outcome to allow unless the base token is no.

When challenge is auth_self:

- prior_grant with auth_admin_keep must not be honored; retain grants do not satisfy auth_self
- prior_grant with auth_admin may satisfy auth_self only when the base token is auth_self or auth_admin

If challenge is set and no prior_grant satisfies it, decision is challenge with the requested challenge echoed.

auth_admin_keep outcomes from rules may be retained per seat for later auth_admin challenges but never for auth_self challenges.
