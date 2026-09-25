use crate::avsc_parse::AvroSchema;
use crate::log_rule::check_logical_constraints;

pub fn logical_types_ok(writer: &AvroSchema, reader: &AvroSchema) -> bool {
    check_logical_constraints(writer, reader).is_empty()
}
