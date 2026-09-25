# Include and substack expansion

@include expands the referenced file inline at the directive location. Paths are relative to the including file directory.

@include-substack pushes a substack frame, expands the referenced file, then pops the frame. Modules from substack files appear once in final order unless another directive references them again.

Nested @include inside a substack file resolves relative to that file directory.
