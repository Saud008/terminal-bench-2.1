# CBOR attestation authData layout

auth_data_hex decodes to bytes with this layout:

- bytes 0..32: rpIdHash
- byte 32: flags
- bytes 33..37: signCount as big-endian u32
- bytes 37..53: AAGUID when AT flag (0x40) is set

Flag bits: UP=0x01, UV=0x04, AT=0x40.

UV must be read from bit 0x04, not 0x02.
