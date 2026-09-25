use crate::model::PacketMeta;
use crate::order;

pub fn arrange_packets(packets: &mut [PacketMeta]) {
    order::global_sort(packets);
}
