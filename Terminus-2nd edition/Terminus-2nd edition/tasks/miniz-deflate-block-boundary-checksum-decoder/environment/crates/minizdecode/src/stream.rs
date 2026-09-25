use crate::adler::AdlerState;
use crate::bitreader::BitReader;
use crate::block_stored;
use crate::errors::DecodeError;
use crate::huffman_dynamic;
use crate::huffman_static;
use crate::ingest;
use crate::staging::{BlockRecord, StagingSnapshot};
use crate::window::Window;

pub struct DecompressResult {
    pub output: Vec<u8>,
    pub staging: StagingSnapshot,
    pub expected_adler: u32,
    pub computed_adler: u32,
}

pub fn decompress_zlib(raw: &[u8]) -> Result<DecompressResult, DecodeError> {
    let expected_adler = ingest::read_zlib_adler(raw)?;
    let bitstream = ingest::strip_zlib_header(raw)?;
    let mut reader = BitReader::new(bitstream);
    let mut window = Window::new();
    let mut out = Vec::new();
    let mut adler = AdlerState::new();
    let mut blocks = Vec::new();
    let mut block_index = 0u32;
    loop {
        let header = reader
            .read_bits(3)
            .map_err(|_| DecodeError::Format("block header".into()))?;
        let final_block = (header & 1) != 0;
        let block_type = (header >> 1) & 0x3;
        let (block_type_name, uncompressed_len, block_checksum) = match block_type {
            0 => {
                let (len, checksum) = block_stored::decode_stored_block(&mut reader, &mut window, &mut out)?;
                if len == 0 && !final_block {
                    break;
                }
                ("stored".to_string(), len, checksum)
            }
            1 => {
                let emitted = huffman_static::decode_fixed_block(&mut reader, &mut window, &mut out)?;
                ("fixed".to_string(), emitted, 0)
            }
            2 => {
                let emitted = huffman_dynamic::decode_dynamic_block(&mut reader, &mut window, &mut out)?;
                ("dynamic".to_string(), emitted, 0)
            }
            _ => return Err(DecodeError::Format("reserved block type".into())),
        };
        let chunk_start = out.len().saturating_sub(uncompressed_len as usize);
        adler.update(&out[chunk_start..]);
        blocks.push(BlockRecord {
            index: block_index,
            block_type: block_type_name,
            final_block,
            uncompressed_len,
            block_checksum,
        });
        block_index += 1;
        if final_block {
            break;
        }
    }
    let staging = StagingSnapshot {
        block_count: blocks.len(),
        blocks,
        window_size: crate::window::WINDOW_SIZE as u32,
        staging_adler: adler.value(),
    };
    Ok(DecompressResult {
        computed_adler: adler.value(),
        expected_adler,
        output: out,
        staging,
    })
}
