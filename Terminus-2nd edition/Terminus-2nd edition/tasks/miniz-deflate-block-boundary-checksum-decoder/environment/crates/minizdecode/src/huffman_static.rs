use crate::bitreader::BitReader;
use crate::errors::DecodeError;
use crate::huffman_dynamic::{decode_huffman_symbols, Huffman};
use crate::window::Window;

pub fn decode_fixed_block(
    reader: &mut BitReader<'_>,
    window: &mut Window,
    out: &mut Vec<u8>,
) -> Result<u16, DecodeError> {
    let lit_lengths = fixed_literal_lengths();
    let dist_lengths = fixed_distance_lengths();
    let lit_tree = Huffman::build(&lit_lengths)?;
    let dist_tree = Huffman::build(&dist_lengths)?;
    decode_huffman_symbols(reader, window, out, &lit_tree, &dist_tree)
}

fn fixed_literal_lengths() -> Vec<u8> {
    let mut lens = vec![0u8; 288];
    lens[..144].fill(8);
    lens[144..256].fill(9);
    lens[256..280].fill(7);
    lens[280..288].fill(8);
    lens
}

fn fixed_distance_lengths() -> Vec<u8> {
    vec![5u8; 32]
}
