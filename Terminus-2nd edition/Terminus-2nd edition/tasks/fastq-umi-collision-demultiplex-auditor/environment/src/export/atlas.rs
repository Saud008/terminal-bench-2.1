use crate::types::AtlasFile;

pub fn atlas_row_count(atlas: &AtlasFile) -> usize {
    atlas.clusters.len() + atlas.contamination_flags.len()
}
