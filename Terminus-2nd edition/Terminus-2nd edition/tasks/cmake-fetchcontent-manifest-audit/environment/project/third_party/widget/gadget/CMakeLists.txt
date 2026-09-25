cmake_minimum_required(VERSION 3.16)
project(gadget C)

include(FetchContent)
include("../../../cmake/WidgetHelpers.cmake")

FetchContent_Declare(libbaz
  URL file:///app/vendor-cache/libbaz-0.9.4.tar.gz
  URL_HASH SHA256=aa025f5b0611a3b21fedf101c9b7417ff36fa083377c388d6868e681335fef5c
)
FetchContent_MakeAvailable(libbaz)

add_library(baz_iface INTERFACE)
target_link_libraries(baz_iface INTERFACE baz)
