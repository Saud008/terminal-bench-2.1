# Delta patch script

After zlib inflate, delta objects yield UTF-8 patch scripts (one opcode per line):

COPY offset length
INSERT suffix-text

COPY copies length bytes from the resolved base window starting at offset bytes from the pre-image window origin (see ofs-delta-window.md). INSERT appends literal suffix bytes to the patch result.

Patch application starts from an empty buffer for ref_delta objects. Seeding the output buffer with the full base payload before COPY opcodes run duplicates base bytes and inflates sizes incorrectly.

Lines are trimmed; blank lines are ignored.
