use crate::bitreader::BitReader;
use crate::errors::DecodeError;
use crate::window::Window;

const CODE_LENGTH_ORDER: [usize; 19] = [
    15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 16, 17, 18,
];

const LENGTH_BASE: [u16; 29] = [
    3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115,
    131, 163, 195, 227, 258,
];
const LENGTH_EXTRA: [u8; 29] = [
    0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0,
];
const DIST_BASE: [u16; 30] = [
    1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537,
    2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577,
];
const DIST_EXTRA: [u8; 30] = [
    0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12,
    13, 13,
];

pub struct Huffman {
    counts: Vec<u16>,
    offsets: Vec<u16>,
    symbols: Vec<u16>,
    max_bits: u32,
}

impl Huffman {
    pub fn build(lengths: &[u8]) -> Result<Self, DecodeError> {
        let max_bits = lengths.iter().copied().max().unwrap_or(0) as u32;
        if max_bits == 0 {
            return Err(DecodeError::Format("empty huffman tree".into()));
        }
        let mut bl_count = vec![0u16; max_bits as usize + 1];
        for &l in lengths {
            if l > 0 {
                bl_count[l as usize] += 1;
            }
        }
        let mut symbols = Vec::new();
        let mut code_lengths: Vec<(u8, u16)> = Vec::new();
        for (sym, &len) in lengths.iter().enumerate() {
            if len > 0 {
                code_lengths.push((len, sym as u16));
            }
        }
        code_lengths.sort_by(|a, b| a.0.cmp(&b.0).then(a.1.cmp(&b.1)));
        for &(_, sym) in &code_lengths {
            symbols.push(sym);
        }
        let mut offsets = vec![0u16; max_bits as usize + 1];
        let mut counts = vec![0u16; max_bits as usize + 1];
        let mut idx = 0u16;
        for len in 1..=max_bits {
            offsets[len as usize] = idx;
            counts[len as usize] = bl_count[len as usize];
            idx += bl_count[len as usize];
        }
        Ok(Self {
            counts,
            offsets,
            symbols,
            max_bits,
        })
    }

    pub fn decode(&self, reader: &mut BitReader<'_>) -> Result<u16, DecodeError> {
        let mut code = 0u32;
        let mut first = 0u32;
        for len in 1..=self.max_bits {
            code = (code << 1)
                | reader
                    .read_bits(1)
                    .map_err(|_| DecodeError::Format("truncated huffman".into()))?;
            let count = u32::from(self.counts[len as usize]);
            if code < first + count {
                let index = self.offsets[len as usize] as u32 + (code - first);
                return Ok(self.symbols[index as usize]);
            }
            first += count;
            first <<= 1;
        }
        Err(DecodeError::Format("invalid huffman code".into()))
    }
}

pub fn decode_huffman_symbols(
    reader: &mut BitReader<'_>,
    window: &mut Window,
    out: &mut Vec<u8>,
    lit_tree: &Huffman,
    dist_tree: &Huffman,
) -> Result<u16, DecodeError> {
    let start_len = out.len();
    loop {
        let sym = lit_tree.decode(reader)?;
        if sym < 256 {
            window.extend(&[sym as u8], out);
        } else if sym == 256 {
            break;
        } else {
            let len_idx = (sym - 257) as usize;
            if len_idx >= LENGTH_BASE.len() {
                return Err(DecodeError::Format("bad length symbol".into()));
            }
            let mut length = u32::from(LENGTH_BASE[len_idx]);
            let extra = LENGTH_EXTRA[len_idx];
            if extra > 0 {
                length += reader.read_bits(extra as u32).map_err(|_| {
                    DecodeError::Format("length extra".into())
                })?;
            }
            let dist_sym = dist_tree.decode(reader)?;
            let dist_idx = dist_sym as usize;
            if dist_idx >= DIST_BASE.len() {
                return Err(DecodeError::Format("bad distance symbol".into()));
            }
            let mut distance = u32::from(DIST_BASE[dist_idx]);
            let dextra = DIST_EXTRA[dist_idx];
            if dextra > 0 {
                distance += reader.read_bits(dextra as u32).map_err(|_| {
                    DecodeError::Format("distance extra".into())
                })?;
            }
            window.copy(distance as usize, length as usize, out);
        }
    }
    Ok((out.len() - start_len) as u16)
}

pub fn decode_dynamic_block(
    reader: &mut BitReader<'_>,
    window: &mut Window,
    out: &mut Vec<u8>,
) -> Result<u16, DecodeError> {
    let hlit = reader.read_bits(5).map_err(|_| DecodeError::Format("hlit".into()))? + 257;
    let hdist = reader.read_bits(5).map_err(|_| DecodeError::Format("hdist".into()))? + 1;
    let hclen = reader.read_bits(4).map_err(|_| DecodeError::Format("hclen".into()))? + 4;
    let mut code_lengths = [0u8; 19];
    for i in 0..hclen {
        let v = reader.read_bits(3).map_err(|_| DecodeError::Format("clen".into()))? as u8;
        code_lengths[CODE_LENGTH_ORDER[i as usize]] = v;
    }
    let cl_tree = Huffman::build(&code_lengths[..19])?;
    let mut lengths = vec![0u8; hlit as usize + hdist as usize];
    let mut i = 0usize;
    while i < lengths.len() {
        let sym = cl_tree.decode(reader)?;
        if sym < 16 {
            lengths[i] = sym as u8;
            i += 1;
        } else if sym == 16 {
            let rep = reader.read_bits(2).map_err(|_| DecodeError::Format("rep".into()))? + 3;
            let prev = if i > 0 { lengths[i - 1] } else { 0 };
            for _ in 0..rep {
                if i >= lengths.len() {
                    break;
                }
                lengths[i] = prev;
                i += 1;
            }
        } else if sym == 17 {
            let rep = reader.read_bits(3).map_err(|_| DecodeError::Format("rep17".into()))? + 3;
            for _ in 0..rep {
                if i >= lengths.len() {
                    break;
                }
                lengths[i] = 0;
                i += 1;
            }
        } else if sym == 18 {
            let rep = reader.read_bits(7).map_err(|_| DecodeError::Format("rep18".into()))? + 11;
            for _ in 0..rep {
                if i >= lengths.len() {
                    break;
                }
                lengths[i] = 0;
                i += 1;
            }
        } else {
            return Err(DecodeError::Format("bad code length symbol".into()));
        }
    }
    let lit_len = Huffman::build(&lengths[..hlit as usize])?;
    let dist_tree = Huffman::build(&lengths[hlit as usize..])?;
    decode_huffman_symbols(reader, window, out, &lit_len, &dist_tree)
}
