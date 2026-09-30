//! Bracket expressions: `[abc]`, `[a-z]`, `[!x]`, `[[:digit:]]`.

/// Matches `tc` against the bracket expression whose body starts at
/// `pat[p]` (just after the `[`). Returns whether the expression accepts
/// `tc` and the index of the closing `]`, or `None` when the expression is
/// malformed, in which case the whole pattern fails.
pub(super) fn bracket(pat: &[u8], mut p: usize, tc: u8) -> Option<(bool, usize)> {
    let at = |i: usize| pat.get(i).copied().unwrap_or(0);
    let negated = at(p) == b'!';
    if negated {
        p += 1;
    }
    let mut prev: u8 = 0;
    let mut matched = false;
    loop {
        let mut pc = at(p);
        if pc == 0 {
            return None;
        }
        if pc == b']' {
            break;
        }
        if pc == b'\\' {
            p += 1;
            pc = at(p);
            if pc == 0 {
                return None;
            }
            if tc == pc {
                matched = true;
            }
        } else if pc == b'-' && prev != 0 && at(p + 1) != 0 && at(p + 1) != b']' {
            p += 1;
            pc = at(p);
            if pc == b'\\' {
                p += 1;
                pc = at(p);
                if pc == 0 {
                    return None;
                }
            }
            if tc <= pc && tc >= prev {
                matched = true;
            }
            pc = 0;
        } else if pc == b'[' && at(p + 1) == b':' {
            let s = p + 2;
            let mut q = s;
            while at(q) != 0 && at(q) != b']' {
                q += 1;
            }
            if at(q) == 0 {
                return None;
            }
            if q == s || pat[q - 1] != b':' {
                // Not a `[:class:]`; the `[` is an ordinary member.
                if tc == pc {
                    matched = true;
                }
            } else {
                match posix_class(&pat[s..q - 1], tc) {
                    Some(true) => matched = true,
                    Some(false) => {}
                    None => return None,
                }
                p = q;
                pc = 0;
            }
        } else if tc == pc {
            matched = true;
        }
        prev = pc;
        p += 1;
    }
    Some((matched != negated, p))
}

fn posix_class(name: &[u8], c: u8) -> Option<bool> {
    Some(match name {
        b"alnum" => c.is_ascii_alphanumeric(),
        b"alpha" => c.is_ascii_alphabetic(),
        b"blank" => c == b' ' || c == b'\t',
        b"cntrl" => c.is_ascii_control(),
        b"digit" => c.is_ascii_digit(),
        b"graph" => c.is_ascii_graphic(),
        b"lower" => c.is_ascii_lowercase(),
        b"print" => c.is_ascii_graphic() || c == b' ',
        b"punct" => c.is_ascii_punctuation(),
        b"space" => c.is_ascii_whitespace(),
        b"upper" => c.is_ascii_uppercase(),
        b"xdigit" => c.is_ascii_hexdigit(),
        _ => return None,
    })
}
