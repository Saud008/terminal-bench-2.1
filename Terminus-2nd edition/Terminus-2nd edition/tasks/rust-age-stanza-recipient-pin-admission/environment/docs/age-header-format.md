# Age header format (v1)

Files under a corpus directory are UTF-8 text (optional binary ciphertext after the header). The governor reads only the ASCII header.

## Layout

1. Magic line exactly: `age-encryption.org/v1`
2. Zero or more recipient stanzas, each on one line:
   - `-> TYPE arg1 [arg2 ...]`
   - `TYPE` is a non-empty token without spaces
   - arguments are space-separated unpadded standard Base64 strings as written on the wire
3. Terminator line exactly: `---`
4. Optional ciphertext bytes after the terminator (ignored for admission)

Blank lines before the magic line are ignored. Any other preamble is a parse failure (`malformed_header`).

## file_id

file_id is the corpus file stem (basename without the final extension). Example: alpha.age maps to file_id alpha.

Default graded corpus stems: alpha, bravo, charlie. The hidden corpus stem is delta. Synthetic malformed probes may use stems such as broken; those must still emit file_id equal to the stem and deny with malformed_header when the header fails the layout rules above. Synthetic overflow probes may use stem overflow when stanza count exceeds max_recipients.
