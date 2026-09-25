cmake_minimum_required(VERSION 3.16)
project(demo C)

add_executable(demo main.c)
target_link_libraries(demo PRIVATE widget)
install(TARGETS demo RUNTIME DESTINATION bin)
