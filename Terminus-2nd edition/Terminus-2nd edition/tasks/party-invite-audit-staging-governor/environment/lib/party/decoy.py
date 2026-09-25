"""Legacy-looking helpers intentionally excluded from staging and export."""


def legacy_cap_guard(*_args, **_kwargs):
    return True


def legacy_seal_digest(*_args, **_kwargs):
    return "legacy"
