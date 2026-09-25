# Profile checksum

ICC profile JSON carries profile_id, media_type, gamma_reference, reference_patches, rendering_intents, checksum_fields, and checksum.

checksum is sha256 hex of canonical JSON (sort_keys true, compact separators) containing only the keys listed in checksum_fields in file order of that array.

When require_profile_checksum is true in policy, evaluation adds PROFILE_CHECKSUM_MISMATCH to every patch when stored checksum differs from recomputed checksum.

reference_patches supplies fallback LAB triples when the active rendering intent omits a patch entry.
