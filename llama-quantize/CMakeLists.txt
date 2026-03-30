cmake_minimum_required(VERSION 3.14)
project("llama-quantize" C CXX)
include(CheckIncludeFileCXX)

# Fix missing C++ standard library headers on macOS (incomplete CommandLineTools installation)
if (APPLE)
    check_include_file_cxx("mutex" HAS_CXX_MUTEX)
    if (NOT HAS_CXX_MUTEX)
        execute_process(COMMAND xcrun --show-sdk-path OUTPUT_VARIABLE MACOS_SDK_PATH OUTPUT_STRIP_TRAILING_WHITESPACE)
        if (EXISTS "${MACOS_SDK_PATH}/usr/include/c++/v1")
            message(STATUS "Adding C++ standard library headers from SDK: ${MACOS_SDK_PATH}/usr/include/c++/v1")
            add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:-isystem;${MACOS_SDK_PATH}/usr/include/c++/v1>")
        endif()
    endif()
endif()

set(CMAKE_WARN_UNUSED_CLI YES)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if (NOT XCODE AND NOT MSVC AND NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Path to the bundled llama.cpp source directory
set(LLAMA_CPP_DIR ${CMAKE_CURRENT_SOURCE_DIR}/llama.cpp)

# Add path to cmake modules
list(APPEND CMAKE_MODULE_PATH "${LLAMA_CPP_DIR}/cmake/")

if (WIN32)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif()

if (MSVC)
    add_compile_options("$<$<COMPILE_LANGUAGE:C>:/utf-8>")
    add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:/utf-8>")
endif()

#
# option list
#

# debug
option(LLAMA_ALL_WARNINGS           "llama: enable all compiler warnings"                   ON)
option(LLAMA_ALL_WARNINGS_3RD_PARTY "llama: enable all compiler warnings in 3rd party libs" OFF)

# build
option(LLAMA_FATAL_WARNINGS "llama: enable -Werror flag" OFF)

# sanitizers
option(LLAMA_SANITIZE_THREAD    "llama: enable thread sanitizer"    OFF)
option(LLAMA_SANITIZE_ADDRESS   "llama: enable address sanitizer"   OFF)
option(LLAMA_SANITIZE_UNDEFINED "llama: enable undefined sanitizer" OFF)

#
# build info
#

include(${LLAMA_CPP_DIR}/cmake/build-info.cmake)
include(${LLAMA_CPP_DIR}/cmake/common.cmake)

# override ggml options
set(GGML_SANITIZE_THREAD    ${LLAMA_SANITIZE_THREAD})
set(GGML_SANITIZE_ADDRESS   ${LLAMA_SANITIZE_ADDRESS})
set(GGML_SANITIZE_UNDEFINED ${LLAMA_SANITIZE_UNDEFINED})
set(GGML_ALL_WARNINGS       ${LLAMA_ALL_WARNINGS})
set(GGML_FATAL_WARNINGS     ${LLAMA_FATAL_WARNINGS})

# change the default for these ggml options
if (NOT DEFINED GGML_LLAMAFILE)
    set(GGML_LLAMAFILE_DEFAULT ON)
endif()

if (NOT DEFINED GGML_CUDA_GRAPHS)
    set(GGML_CUDA_GRAPHS_DEFAULT ON)
endif()

#
# build ggml
#

if (NOT TARGET ggml)
    add_subdirectory(${LLAMA_CPP_DIR}/ggml ${CMAKE_CURRENT_BINARY_DIR}/ggml)
endif()

#
# build llama library
#

llama_add_compile_flags()

add_library(llama
    ${LLAMA_CPP_DIR}/include/llama.h
    ${LLAMA_CPP_DIR}/src/llama.cpp
    ${LLAMA_CPP_DIR}/src/llama-vocab.cpp
    ${LLAMA_CPP_DIR}/src/llama-grammar.cpp
    ${LLAMA_CPP_DIR}/src/llama-sampling.cpp
    ${LLAMA_CPP_DIR}/src/unicode.h
    ${LLAMA_CPP_DIR}/src/unicode.cpp
    ${LLAMA_CPP_DIR}/src/unicode-data.cpp
)

target_include_directories(llama PUBLIC ${LLAMA_CPP_DIR}/src ${LLAMA_CPP_DIR}/include)
target_compile_features(llama PUBLIC cxx_std_17)
target_link_libraries(llama PUBLIC ggml)

if (BUILD_SHARED_LIBS)
    set_target_properties(llama PROPERTIES POSITION_INDEPENDENT_CODE ON)
    target_compile_definitions(llama PRIVATE LLAMA_BUILD)
    target_compile_definitions(llama PUBLIC  LLAMA_SHARED)
endif()

#
# build common library
#

find_package(Threads REQUIRED)

# Generate build-info.cpp
if(EXISTS "${LLAMA_CPP_DIR}/.git")
    set(GIT_DIR "${LLAMA_CPP_DIR}/.git")

    if(NOT IS_DIRECTORY "${GIT_DIR}")
        file(READ ${GIT_DIR} REAL_GIT_DIR_LINK)
        string(REGEX REPLACE "gitdir: (.*)\n$" "\\1" REAL_GIT_DIR ${REAL_GIT_DIR_LINK})
        string(FIND "${REAL_GIT_DIR}" "/" SLASH_POS)
        if (SLASH_POS EQUAL 0)
            set(GIT_DIR "${REAL_GIT_DIR}")
        else()
            set(GIT_DIR "${LLAMA_CPP_DIR}/${REAL_GIT_DIR}")
        endif()
    endif()

    if(EXISTS "${GIT_DIR}/index")
        set(GIT_INDEX "${GIT_DIR}/index")
    else()
        set(GIT_INDEX "")
    endif()
else()
    set(GIT_INDEX "")
endif()

add_custom_command(
    OUTPUT "${LLAMA_CPP_DIR}/common/build-info.cpp"
    COMMENT "Generating build details from Git"
    COMMAND ${CMAKE_COMMAND} -DMSVC=${MSVC} -DCMAKE_C_COMPILER_VERSION=${CMAKE_C_COMPILER_VERSION}
            -DCMAKE_C_COMPILER_ID=${CMAKE_C_COMPILER_ID} -DCMAKE_VS_PLATFORM_NAME=${CMAKE_VS_PLATFORM_NAME}
            -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER} -P "${LLAMA_CPP_DIR}/common/cmake/build-info-gen-cpp.cmake"
    WORKING_DIRECTORY "${LLAMA_CPP_DIR}"
    DEPENDS "${LLAMA_CPP_DIR}/common/build-info.cpp.in" ${GIT_INDEX}
    VERBATIM
)

add_library(build_info OBJECT ${LLAMA_CPP_DIR}/common/build-info.cpp)
if (BUILD_SHARED_LIBS)
    set_target_properties(build_info PROPERTIES POSITION_INDEPENDENT_CODE ON)
endif()

add_library(common STATIC
    ${LLAMA_CPP_DIR}/common/arg.cpp
    ${LLAMA_CPP_DIR}/common/arg.h
    ${LLAMA_CPP_DIR}/common/base64.hpp
    ${LLAMA_CPP_DIR}/common/common.cpp
    ${LLAMA_CPP_DIR}/common/common.h
    ${LLAMA_CPP_DIR}/common/console.cpp
    ${LLAMA_CPP_DIR}/common/console.h
    ${LLAMA_CPP_DIR}/common/json-schema-to-grammar.cpp
    ${LLAMA_CPP_DIR}/common/json.hpp
    ${LLAMA_CPP_DIR}/common/log.cpp
    ${LLAMA_CPP_DIR}/common/log.h
    ${LLAMA_CPP_DIR}/common/ngram-cache.cpp
    ${LLAMA_CPP_DIR}/common/ngram-cache.h
    ${LLAMA_CPP_DIR}/common/sampling.cpp
    ${LLAMA_CPP_DIR}/common/sampling.h
    ${LLAMA_CPP_DIR}/common/speculative.cpp
    ${LLAMA_CPP_DIR}/common/speculative.h
)

if (BUILD_SHARED_LIBS)
    set_target_properties(common PROPERTIES POSITION_INDEPENDENT_CODE ON)
endif()

target_include_directories(common PUBLIC ${LLAMA_CPP_DIR}/common)
target_compile_features(common PUBLIC cxx_std_17)
target_link_libraries(common PRIVATE build_info PUBLIC llama Threads::Threads)

#
# build llama-quantize executable
#

add_executable(llama-quantize ${LLAMA_CPP_DIR}/examples/quantize/quantize.cpp)
install(TARGETS llama-quantize RUNTIME)
target_link_libraries(llama-quantize PRIVATE common llama ${CMAKE_THREAD_LIBS_INIT})
target_include_directories(llama-quantize PRIVATE ${LLAMA_CPP_DIR}/common)
target_compile_features(llama-quantize PRIVATE cxx_std_17)
