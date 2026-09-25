pub mod block;
pub mod crc;
pub mod epb;
pub mod interface;

pub const BT_SHB: u32 = 0x0A0D0D0A;
pub const BT_IDB: u32 = 0x00000001;
pub const BT_EPB: u32 = 0x00000006;
pub const OPT_IF_NAME: u16 = 2;
pub const OPT_EPB_CRC: u16 = 0x0EBC;
pub const OPT_END: u16 = 0;
