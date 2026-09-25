pub mod dimension_facet;

pub fn facet_count_ok(ndims: usize, index_ndims: usize) -> bool {
    dimension_facet::matches_catalog(ndims, index_ndims)
}
