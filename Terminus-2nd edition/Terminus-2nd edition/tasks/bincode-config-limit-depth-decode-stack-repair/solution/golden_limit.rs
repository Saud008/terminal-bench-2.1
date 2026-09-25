use crate::error::{DecodeError, LimitKind};

#[derive(Debug, Clone)]
pub struct LimitTracker {
    pub remaining_depth: u32,
    pub remaining_bytes: u64,
    frames: Vec<u32>,
}

impl LimitTracker {
    pub fn new(max_depth: u32, max_bytes: u64) -> Self {
        Self {
            remaining_depth: max_depth,
            remaining_bytes: max_bytes,
            frames: Vec::new(),
        }
    }

    pub fn bytes_consumed(&self, max_bytes: u64) -> u64 {
        max_bytes.saturating_sub(self.remaining_bytes)
    }

    pub fn enter_composite(&mut self) -> Result<(), DecodeError> {
        if self.remaining_depth == 0 {
            return Err(DecodeError::LimitExceeded {
                kind: LimitKind::Depth,
            });
        }
        self.frames.push(self.remaining_depth);
        self.remaining_depth -= 1;
        Ok(())
    }

    pub fn leave_composite(&mut self) {
        if let Some(restored) = self.frames.pop() {
            self.remaining_depth = restored;
        }
    }

    pub fn charge_byte(&mut self) -> Result<(), DecodeError> {
        if self.remaining_bytes == 0 {
            return Err(DecodeError::LimitExceeded {
                kind: LimitKind::Bytes,
            });
        }
        self.remaining_bytes -= 1;
        Ok(())
    }

    pub fn charge_bytes(&mut self, n: usize) -> Result<(), DecodeError> {
        for _ in 0..n {
            self.charge_byte()?;
        }
        Ok(())
    }
}
