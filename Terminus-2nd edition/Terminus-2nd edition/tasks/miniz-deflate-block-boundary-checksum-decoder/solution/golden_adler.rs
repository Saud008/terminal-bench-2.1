const MOD: u32 = 65521;

pub struct AdlerState {
    a: u32,
    b: u32,
}

impl AdlerState {
    pub fn new() -> Self {
        Self { a: 1, b: 0 }
    }

    pub fn update(&mut self, data: &[u8]) {
        for &byte in data {
            self.a = (self.a + u32::from(byte)) % MOD;
            self.b = (self.b + self.a) % MOD;
        }
    }

    pub fn value(&self) -> u32 {
        (self.b << 16) | self.a
    }
}

pub fn adler32(data: &[u8]) -> u32 {
    let mut state = AdlerState::new();
    state.update(data);
    state.value()
}
