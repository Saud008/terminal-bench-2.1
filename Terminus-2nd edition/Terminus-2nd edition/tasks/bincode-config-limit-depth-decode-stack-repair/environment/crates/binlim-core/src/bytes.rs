use crate::error::DecodeError;
use crate::limit::LimitTracker;

pub struct ByteReader<'a> {
    data: &'a [u8],
    pos: usize,
    pub(crate) limits: &'a mut LimitTracker,
}

impl<'a> ByteReader<'a> {
    pub fn new(data: &'a [u8], limits: &'a mut LimitTracker) -> Self {
        Self {
            data,
            pos: 0,
            limits,
        }
    }

    pub fn remaining_slice(&self) -> &[u8] {
        &self.data[self.pos..]
    }

    pub fn read_byte(&mut self) -> Result<u8, DecodeError> {
        if self.pos >= self.data.len() {
            return Err(DecodeError::UnexpectedEof);
        }
        self.limits.charge_byte()?;
        let b = self.data[self.pos];
        self.pos += 1;
        Ok(b)
    }

    pub fn read_varint_body(&mut self) -> Result<u32, DecodeError> {
        let start = self.pos;
        let mut value: u32 = 0;
        let mut shift = 0;
        loop {
            if self.pos >= self.data.len() {
                return Err(DecodeError::UnexpectedEof);
            }
            let b = self.data[self.pos];
            self.pos += 1;
            value |= ((b & 0x7f) as u32) << shift;
            if b & 0x80 == 0 {
                break;
            }
            shift += 7;
            if shift > 28 {
                return Err(DecodeError::InvalidVarint);
            }
        }
        let consumed = self.pos - start;
        let _ = consumed;
        Ok(value)
    }

    pub fn read_exact(&mut self, n: usize) -> Result<&[u8], DecodeError> {
        if self.pos + n > self.data.len() {
            return Err(DecodeError::UnexpectedEof);
        }
        self.limits.charge_bytes(n)?;
        let slice = &self.data[self.pos..self.pos + n];
        self.pos += n;
        Ok(slice)
    }

    pub fn charge_tag_only(&mut self) -> Result<(), DecodeError> {
        self.limits.charge_byte()
    }
}
