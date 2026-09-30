//! Glob matching with git's wildmatch rules.
//!
//! With `pathname` set, `*`, `?` and bracket expressions never match `/`.
//! Without it every `*` may match `/` (only used for single components).

use super::charclass;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Outcome {
    Match,
    NoMatch,
    AbortAll,
    AbortToStarStar,
}

pub fn wildmatch(pattern: &[u8], text: &[u8], pathname: bool) -> bool {
    dowild(pattern, 0, text, 0, pathname) == Outcome::Match
}

fn is_glob_special(c: u8) -> bool {
    matches!(c, b'*' | b'?' | b'[' | b'\\')
}

fn dowild(pat: &[u8], mut p: usize, text: &[u8], mut t: usize, pathname: bool) -> Outcome {
    while p < pat.len() {
        let p_ch = pat[p];
        let t_ch = text.get(t).copied();
        if t_ch.is_none() && p_ch != b'*' {
            return Outcome::AbortAll;
        }
        match p_ch {
            b'\\' => {
                p += 1;
                if pat.get(p).copied() != t_ch {
                    return Outcome::NoMatch;
                }
            }
            b'?' => {
                if pathname && t_ch == Some(b'/') {
                    return Outcome::NoMatch;
                }
            }
            b'*' => return star(pat, p, text, t, pathname),
            b'[' => {
                let tc = t_ch.unwrap_or(0);
                match charclass::bracket(pat, p + 1, tc) {
                    None => return Outcome::AbortAll,
                    Some((hit, end)) => {
                        if !hit || (pathname && tc == b'/') {
                            return Outcome::NoMatch;
                        }
                        p = end;
                    }
                }
            }
            _ => {
                if t_ch != Some(p_ch) {
                    return Outcome::NoMatch;
                }
            }
        }
        p += 1;
        t += 1;
    }
    if t < text.len() {
        Outcome::NoMatch
    } else {
        Outcome::Match
    }
}

/// Handles a run of `*` starting at `pat[p]`.
fn star(pat: &[u8], mut p: usize, text: &[u8], mut t: usize, pathname: bool) -> Outcome {
    p += 1;
    let match_slash = if pat.get(p) == Some(&b'*') {
        while pat.get(p) == Some(&b'*') {
            p += 1;
        }
        true
    } else {
        !pathname
    };

    if p == pat.len() {
        if !match_slash && text[t..].contains(&b'/') {
            return Outcome::NoMatch;
        }
        return Outcome::Match;
    }
    if !match_slash && pat[p] == b'/' {
        // A single `*` followed by `/` swallows the rest of this component.
        let Some(off) = text[t..].iter().position(|&c| c == b'/') else {
            return Outcome::NoMatch;
        };
        t += off;
        return dowild(pat, p + 1, text, t + 1, pathname);
    }

    let mut t_ch = text.get(t).copied();
    while t_ch.is_some() {
        if !is_glob_special(pat[p]) {
            let lit = pat[p];
            while let Some(c) = text.get(t).copied() {
                if (!match_slash && c == b'/') || c == lit {
                    break;
                }
                t += 1;
            }
            t_ch = text.get(t).copied();
            if t_ch != Some(lit) {
                return if match_slash { Outcome::AbortAll } else { Outcome::AbortToStarStar };
            }
        }
        let matched = dowild(pat, p, text, t, pathname);
        if matched != Outcome::NoMatch {
            if !match_slash || matched != Outcome::AbortToStarStar {
                return matched;
            }
        } else if !match_slash && t_ch == Some(b'/') {
            return Outcome::AbortToStarStar;
        }
        t += 1;
        t_ch = text.get(t).copied();
    }
    Outcome::AbortAll
}
