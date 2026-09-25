pub const WINDOW_SIZE: usize = 32768;

pub struct Window {
    buf: [u8; WINDOW_SIZE],
    pos: usize,
    filled: usize,
}

impl Window {
    pub fn new() -> Self {
        Self {
            buf: [0u8; WINDOW_SIZE],
            pos: 0,
            filled: 0,
        }
    }

    pub fn extend(&mut self, data: &[u8], out: &mut Vec<u8>) {
        for &b in data {
            self.buf[self.pos] = b;
            self.pos = (self.pos + 1) % WINDOW_SIZE;
            if self.filled < WINDOW_SIZE {
                self.filled += 1;
            }
            out.push(b);
        }
    }

    pub fn copy(&mut self, dist: usize, len: usize, out: &mut Vec<u8>) {
        for _ in 0..len {
            let src = (self.pos + WINDOW_SIZE - (dist % WINDOW_SIZE)) % WINDOW_SIZE;
            let b = self.buf[src];
            self.buf[self.pos] = b;
            self.pos = (self.pos + 1) % WINDOW_SIZE;
            if self.filled < WINDOW_SIZE {
                self.filled += 1;
            }
            out.push(b);
        }
    }
}
