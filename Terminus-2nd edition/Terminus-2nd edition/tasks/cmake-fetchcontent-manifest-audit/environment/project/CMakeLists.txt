cmake_minimum_required(VERSION 3.16)
project(widget_demo C)

include("overlays/pinned.cmake")

add_subdirectory(third_party/widget)
add_subdirectory(src)

install(FILES include/widget.h DESTINATION include)
