use crate::bytes::ByteReader;
use crate::error::DecodeError;
use crate::limit::LimitTracker;
use crate::model::{DecodedValue, DoubleOptionInner};
use crate::varint::read_varint;

pub struct Visitor<'a> {
    reader: ByteReader<'a>,
}

impl<'a> Visitor<'a> {
    pub fn new(data: &'a [u8], limits: &'a mut LimitTracker) -> Self {
        Self {
            reader: ByteReader::new(data, limits),
        }
    }

    pub fn decode_value(&mut self) -> Result<DecodedValue, DecodeError> {
        let tag = self.reader.read_byte()?;
        match tag {
            0 => Ok(DecodedValue::Null),
            1 => {
                let b = self.reader.read_byte()?;
                Ok(DecodedValue::Bool { value: b != 0 })
            }
            2 => {
                let v = read_varint(&mut self.reader)?;
                Ok(DecodedValue::U32 { value: v })
            }
            3 => self.decode_string(),
            4 => self.decode_vec(),
            5 => self.decode_enum(),
            6 => self.decode_double_option(),
            other => Err(DecodeError::InvalidTag(other)),
        }
    }

    fn decode_string(&mut self) -> Result<DecodedValue, DecodeError> {
        let len = self.reader.read_varint_body()? as usize;
        let raw = self.reader.read_exact(len)?;
        let s = std::str::from_utf8(raw)
            .map_err(|_| DecodeError::InvalidTag(3))?
            .to_string();
        Ok(DecodedValue::String { value: s })
    }

    fn decode_vec(&mut self) -> Result<DecodedValue, DecodeError> {
        let count = self.reader.read_varint_body()? as usize;
        self.reader.limits.enter_composite()?;
        let mut items = Vec::with_capacity(count);
        for _ in 0..count {
            items.push(self.decode_value()?);
        }
        self.reader.limits.leave_composite();
        Ok(DecodedValue::Vec { items })
    }

    fn decode_enum(&mut self) -> Result<DecodedValue, DecodeError> {
        let variant = self.reader.read_varint_body()?;
        self.reader.limits.enter_composite()?;
        let payload = self.decode_value()?;
        self.reader.limits.leave_composite();
        Ok(DecodedValue::Enum {
            tag: variant,
            payload: Box::new(payload),
        })
    }

    fn decode_double_option(&mut self) -> Result<DecodedValue, DecodeError> {
        let outer = self.reader.read_byte()?;
        if outer == 0 {
            return Ok(DecodedValue::DoubleOption {
                value: DoubleOptionInner::none(),
            });
        }
        self.reader.limits.enter_composite()?;
        self.reader.limits.enter_composite()?;
        let inner = self.reader.read_byte()?;
        if inner == 0 {
            self.reader.limits.leave_composite();
            self.reader.limits.leave_composite();
            return Ok(DecodedValue::DoubleOption {
                value: DoubleOptionInner::some_none(),
            });
        }
        let nested = self.decode_value()?;
        self.reader.limits.leave_composite();
        self.reader.limits.leave_composite();
        Ok(DecodedValue::DoubleOption {
            value: DoubleOptionInner::some_some(nested),
        })
    }
}
