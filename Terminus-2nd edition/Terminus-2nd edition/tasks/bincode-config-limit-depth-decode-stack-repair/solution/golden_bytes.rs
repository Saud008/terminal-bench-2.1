use crate::error::DecodeError;
use crate::limit::LimitTracker;
use crate::varint::read_varint;

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
        read_varint(self)
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
}
