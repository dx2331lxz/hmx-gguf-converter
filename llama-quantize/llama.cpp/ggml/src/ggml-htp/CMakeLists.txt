message(STATUS "Using My Hexagon backend")

set(GGML_SOURCES_HTP 
    ggml-htp.cc
    dsprpc_interface.h
    dsprpc_interface.cc
    ggml-htp-impl.h
    htp-cpu-impl.c
    htp-ops.cc
    htp-ops.h
    rpcmem_mapper.cc
    rpcmem_mapper.h
)

ggml_add_backend_library(ggml-htp ${GGML_SOURCES_HTP})

# Link ggml-cpu to resolve quantization function symbols
target_link_libraries(ggml-htp PRIVATE ggml-cpu)
