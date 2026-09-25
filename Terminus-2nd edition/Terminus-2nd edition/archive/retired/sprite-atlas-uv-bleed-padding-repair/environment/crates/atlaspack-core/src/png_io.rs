use crate::model::AtlasError;
use png::{BitDepth, ColorType, Decoder, Encoder, Transformations};
use std::fs::File;
use std::io::{BufReader, BufWriter};
use std::path::Path;

pub fn read_png(path: &Path) -> Result<Vec<u8>, AtlasError> {
    let file = File::open(path).map_err(|e| AtlasError::Io(e.to_string()))?;
    let reader = BufReader::new(file);
    let mut decoder = Decoder::new(reader);
    decoder.set_transformations(Transformations::EXPAND | Transformations::STRIP_16);
    let mut reader = decoder
        .read_info()
        .map_err(|e| AtlasError::Parse(e.to_string()))?;
    let info = reader.info();
    let w = info.width as usize;
    let h = info.height as usize;
    let color_type = info.color_type;
    let mut buf = vec![0u8; reader.output_buffer_size()];
    let frame = reader
        .next_frame(&mut buf)
        .map_err(|e| AtlasError::Parse(e.to_string()))?;
    let bytes = &buf[..frame.buffer_size()];
    match color_type {
        ColorType::Rgba => Ok(bytes.to_vec()),
        ColorType::Rgb => {
            let mut rgba = Vec::with_capacity(w * h * 4);
            for chunk in bytes.chunks_exact(3) {
                rgba.extend_from_slice(&[chunk[0], chunk[1], chunk[2], 255]);
            }
            Ok(rgba)
        }
        ColorType::Grayscale => {
            let mut rgba = Vec::with_capacity(w * h * 4);
            for &g in bytes {
                rgba.extend_from_slice(&[g, g, g, 255]);
            }
            Ok(rgba)
        }
        ColorType::GrayscaleAlpha => {
            let mut rgba = Vec::with_capacity(w * h * 4);
            for chunk in bytes.chunks_exact(2) {
                rgba.extend_from_slice(&[chunk[0], chunk[0], chunk[0], chunk[1]]);
            }
            Ok(rgba)
        }
        _ => Err(AtlasError::Parse("unsupported png color type".into())),
    }
}

pub fn read_png_size(path: &Path) -> Result<(u32, u32, Vec<u8>), AtlasError> {
    let rgba = read_png(path)?;
    let file = File::open(path).map_err(|e| AtlasError::Io(e.to_string()))?;
    let reader = BufReader::new(file);
    let mut decoder = Decoder::new(reader);
    let info = decoder
        .read_header_info()
        .map_err(|e| AtlasError::Parse(e.to_string()))?;
    Ok((info.width, info.height, rgba))
}

pub fn write_png(path: &Path, width: u32, height: u32, rgba: &[u8]) -> Result<(), AtlasError> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| AtlasError::Io(e.to_string()))?;
    }
    let file = File::create(path).map_err(|e| AtlasError::Io(e.to_string()))?;
    let writer = BufWriter::new(file);
    let mut encoder = Encoder::new(writer, width, height);
    encoder.set_color(ColorType::Rgba);
    encoder.set_depth(BitDepth::Eight);
    let mut writer = encoder
        .write_header()
        .map_err(|e| AtlasError::Io(e.to_string()))?;
    writer
        .write_image_data(rgba)
        .map_err(|e| AtlasError::Io(e.to_string()))?;
    Ok(())
}

pub fn resize_nearest(src: &[u8], sw: u32, sh: u32, dw: u32, dh: u32) -> Vec<u8> {
    let mut out = vec![0u8; (dw * dh * 4) as usize];
    for y in 0..dh {
        for x in 0..dw {
            let sx = (x as u64 * sw as u64 / dw as u64) as u32;
            let sy = (y as u64 * sh as u64 / dh as u64) as u32;
            let si = ((sy * sw + sx) * 4) as usize;
            let di = ((y * dw + x) * 4) as usize;
            out[di..di + 4].copy_from_slice(&src[si..si + 4]);
        }
    }
    out
}

pub fn rotate_cw(src: &[u8], w: u32, h: u32) -> (u32, u32, Vec<u8>) {
    let nw = h;
    let nh = w;
    let mut out = vec![0u8; (nw * nh * 4) as usize];
    for y in 0..h {
        for x in 0..w {
            let si = ((y * w + x) * 4) as usize;
            let nx = h - 1 - y;
            let ny = x;
            let di = ((ny * nw + nx) * 4) as usize;
            out[di..di + 4].copy_from_slice(&src[si..si + 4]);
        }
    }
    (nw, nh, out)
}
