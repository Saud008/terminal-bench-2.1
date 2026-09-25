# FIX checksum and body length

Session files are raw bytes with one or more FIX 4.2 messages. Each message uses ASCII SOH (`0x01`) as the field delimiter.

## Body length (tag 9)

`BodyLength` is the byte count of the message body: every byte **after** the SOH that follows the `9=<value>` field, up to but **not including** the `CheckSum` field (`10=`).

The body does **not** include `8=FIX.4.2`, tag 9, or tag 10.

## Checksum (tag 10)

1. Build the message through the SOH that precedes `10=`.
2. Sum every byte from the start of the message through that SOH (do not include `10=` or the checksum digits).
3. Take the sum modulo 256.
4. Append `10=` plus the three-digit zero-padded checksum and a trailing SOH.

Ingest must reject any message whose declared body length or checksum does not match the rules above. Truncated messages (body shorter than tag 9) must fail ingest with a non-zero exit code.
