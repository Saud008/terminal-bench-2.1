//! TZif (RFC 8536) reader. Only the version 2+ 64-bit block and the footer
//! rule are used; version 1 files fall back to the 32-bit block.

use super::rule::PosixRule;
use crate::civil::{breakdown, Tm};

#[derive(Debug, Clone, Copy)]
pub struct TType {
    pub utoff: i64,
    pub isdst: bool,
}

#[derive(Debug, Clone)]
pub struct TzData {
    pub transitions: Vec<i64>,
    pub idxs: Vec<u8>,
    pub types: Vec<TType>,
    pub footer: Option<PosixRule>,
}

struct Header {
    version: u8,
    isutcnt: usize,
    isstdcnt: usize,
    leapcnt: usize,
    timecnt: usize,
    typecnt: usize,
    charcnt: usize,
}

fn be32(b: &[u8]) -> i64 {
    i32::from_be_bytes([b[0], b[1], b[2], b[3]]) as i64
}

fn be64(b: &[u8]) -> i64 {
    i64::from_be_bytes([b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7]])
}

fn header(b: &[u8]) -> Option<Header> {
    if b.len() < 44 || &b[0..4] != b"TZif" {
        return None;
    }
    let n = |i: usize| be32(&b[20 + 4 * i..]) as usize;
    Some(Header {
        version: b[4],
        isutcnt: n(0),
        isstdcnt: n(1),
        leapcnt: n(2),
        timecnt: n(3),
        typecnt: n(4),
        charcnt: n(5),
    })
}

fn block_len(h: &Header, tsize: usize) -> usize {
    h.timecnt * tsize
        + h.timecnt
        + h.typecnt * 6
        + h.charcnt
        + h.leapcnt * (tsize + 4)
        + h.isstdcnt
        + h.isutcnt
}

fn read_block(b: &[u8], h: &Header, tsize: usize) -> Option<(Vec<i64>, Vec<u8>, Vec<TType>)> {
    if b.len() < block_len(h, tsize) {
        return None;
    }
    let mut p = 0;
    let mut transitions = Vec::with_capacity(h.timecnt);
    for _ in 0..h.timecnt {
        let v = if tsize == 8 { be64(&b[p..]) } else { be32(&b[p..]) };
        transitions.push(v);
        p += tsize;
    }
    let idxs = b[p..p + h.timecnt].to_vec();
    p += h.timecnt;
    let mut types = Vec::with_capacity(h.typecnt);
    for _ in 0..h.typecnt {
        types.push(TType {
            utoff: be32(&b[p..]),
            isdst: b[p + 4] != 0,
        });
        p += 6;
    }
    if idxs.iter().any(|&i| i as usize >= types.len()) {
        return None;
    }
    Some((transitions, idxs, types))
}

pub fn parse(b: &[u8]) -> Option<TzData> {
    let h1 = header(b)?;
    let v1_len = 44 + block_len(&h1, 4);
    if h1.version == 0 {
        let (transitions, idxs, types) = read_block(&b[44..], &h1, 4)?;
        return Some(TzData { transitions, idxs, types, footer: None });
    }

    let rest = b.get(v1_len..)?;
    let h2 = header(rest)?;
    let body = &rest[44..];
    let (transitions, idxs, types) = read_block(body, &h2, 8)?;
    let tail = &body[block_len(&h2, 8)..];
    let footer = if tail.first() == Some(&b'\n') {
        let end = tail[1..].iter().position(|&c| c == b'\n')?;
        let s = std::str::from_utf8(&tail[1..1 + end]).ok()?;
        if s.is_empty() {
            None
        } else {
            PosixRule::parse(s)
        }
    } else {
        None
    };
    if types.is_empty() {
        return None;
    }
    Some(TzData { transitions, idxs, types, footer })
}

impl TzData {
    fn type_at(&self, t: i64) -> Option<TType> {
        let n = self.transitions.len();
        if n == 0 || t < self.transitions[0] {
            let first = self.types.iter().find(|ty| !ty.isdst).unwrap_or(&self.types[0]);
            return Some(*first);
        }
        if t >= self.transitions[n - 1] {
            if self.footer.is_some() {
                return None;
            }
            return Some(self.types[self.idxs[n - 1] as usize]);
        }
        let i = self.transitions.partition_point(|&x| x <= t);
        Some(self.types[self.idxs[i - 1] as usize])
    }

    pub fn localtime(&self, t: i64) -> Tm {
        match self.type_at(t) {
            Some(ty) => breakdown(t, ty.utoff, ty.isdst as i32),
            None => {
                let rule = self.footer.as_ref().expect("footer rule");
                let (utoff, isdst) = rule.offset_at(t);
                breakdown(t, utoff, isdst as i32)
            }
        }
    }
}
