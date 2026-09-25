pub const WINDOW_SIZE: usize = 32768;

pub struct Window {
    buf: Vec<u8>,
    pos: usize,
}

impl Window {
    pub fn new() -> Self {
        Self {
            buf: Vec::with_capacity(WINDOW_SIZE),
            pos: 0,
        }
    }

    pub fn extend(&mut self, data: &[u8], out: &mut Vec<u8>) {
        for &b in data {
            self.buf.push(b);
            if self.buf.len() > WINDOW_SIZE {
                self.buf.remove(0);
            }
            out.push(b);
            self.pos += 1;
        }
    }

    pub fn copy(&mut self, dist: usize, len: usize, out: &mut Vec<u8>) {
        for _ in 0..len {
            let idx = self.buf.len().saturating_sub(dist);
            let b = self.buf.get(idx).copied().unwrap_or(0);
            self.buf.push(b);
            if self.buf.len() > WINDOW_SIZE {
                self.buf.remove(0);
            }
            out.push(b);
        }
    }
}
