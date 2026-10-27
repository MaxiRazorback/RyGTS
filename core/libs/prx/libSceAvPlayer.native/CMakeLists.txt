add_library(libSceAvPlayer.native SHARED EXCLUDE_FROM_ALL ${CMAKE_CURRENT_SOURCE_DIR}/Export.cpp)
target_include_directories(libSceAvPlayer.native PRIVATE ${LIBS_INCLUDE_DIR})
set_target_properties(libSceAvPlayer.native PROPERTIES CXX_EXTENSIONS OFF)
configure_windows_unwind(libSceAvPlayer.native)
# Movie decoding (MP4 demuxing, H.264 / HEVC / AAC).
target_link_libraries(libSceAvPlayer.native PRIVATE ffmpeg)
# Only the demuxer and decoders it uses (the whole FFmpeg is ~35 MB).
target_link_options(libSceAvPlayer.native PRIVATE -Wl,--gc-sections -s)

if(MINGW)
    foreach(runtimeLinkFlag IN ITEMS -static-libgcc -static-libstdc++ -static)
        string(REPLACE "${runtimeLinkFlag}" "" CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS}")
    endforeach()
endif()
