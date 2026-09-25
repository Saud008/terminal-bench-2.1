pub struct BitReader<'a> {
    data: &'a [u8],
    pos: usize,
    bitbuf: u32,
    nbits: u32,
}

impl<'a> BitReader<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        Self {
            data,
            pos: 0,
            bitbuf: 0,
            nbits: 0,
        }
    }

    pub fn align_byte(&mut self) {
        self.nbits = 0;
        self.bitbuf = 0;
    }

    pub fn read_bits(&mut self, count: u32) -> Result<u32, ()> {
        while self.nbits < count {
            if self.pos >= self.data.len() {
                return Err(());
            }
            self.bitbuf |= (self.data[self.pos] as u32) << self.nbits;
            self.pos += 1;
            self.nbits += 8;
        }
        let mask = (1u32 << count) - 1;
        let value = self.bitbuf & mask;
        self.bitbuf >>= count;
        self.nbits -= count;
        Ok(value)
    }

    pub fn remaining(&self) -> usize {
        self.data.len().saturating_sub(self.pos)
    }

    pub fn position(&self) -> usize {
        self.pos
    }

    pub fn data(&self) -> &[u8] {
        self.data
    }

    pub fn skip(&mut self, n: usize) {
        self.pos = self.pos.saturating_add(n);
    }

    pub fn read_bytes(&mut self, n: usize) -> Result<&[u8], ()> {
        if self.remaining() < n {
            return Err(());
        }
        let start = self.pos;
        self.pos += n;
        Ok(&self.data[start..start + n])
    }
}
