# PEP 440 version rank ladder

Compare versions by epoch first when a colon prefix is present. Compare release segments left to right using numeric parts when both segments are digits. A tilde suffix on a release segment sorts before the same segment without tilde. Post releases with .postN sort after the final release. Local segments after + sort after the same version without local.

When two candidate versions tie on wheel tag rank, emit must select the PEP 440 highest version.
