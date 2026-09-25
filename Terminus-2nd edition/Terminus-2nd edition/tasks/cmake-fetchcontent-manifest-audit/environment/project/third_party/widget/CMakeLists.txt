cmake_minimum_required(VERSION 3.16)
project(widget C)

include(FetchContent)

FetchContent_Declare(libfoo
  URL file:///app/vendor-cache/libfoo-1.0.0.tar.gz
  URL_HASH SHA256=faa56e9d46400d681f3763a123e2efa2e39e94c1860092ff6c8f7879cf3e13b1
)
FetchContent_MakeAvailable(libfoo)

FetchContent_Declare(libbar
  URL file:///app/vendor-cache/libbar-2.1.0.tar.gz
  URL_HASH SHA256=72b6653cd93eb91ba456d39299548eaed2502e9f6cc66354329b000cac61a2d4
)
FetchContent_MakeAvailable(libbar)

add_subdirectory(gadget)

add_library(widget STATIC widget.c)
target_link_libraries(widget PUBLIC foo bar baz_iface)
target_include_directories(widget PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
install(TARGETS widget ARCHIVE DESTINATION lib)
