project (kaitai_struct_awkward_runtime CXX)
cmake_minimum_required (VERSION 3.3)

set (CMAKE_INCLUDE_CURRENT_DIR ON)

find_package(ZLIB)

find_path(ICONV_INCLUDE_DIRS iconv.h)
mark_as_advanced(ICONV_INCLUDE_DIRS)
find_library(ICONV_LIBRARIES NAMES libiconv libiconv-2 iconv)
mark_as_advanced(ICONV_LIBRARIES)

# Download headers
include(FetchContent)
set(AWKWARD_VERSION "v2.1.0")
FetchContent_Declare(
  awkward-headers
  URL https://github.com/scikit-hep/awkward/releases/download/${AWKWARD_VERSION}/header-only.zip)
# Instead of using `FetchContent_MakeAvailable(awkward-headers)`, we manually load the target so
# that we can EXCLUDE_FROM_ALL
FetchContent_GetProperties(awkward-headers)
if(NOT awkward-headers_POPULATED)
  FetchContent_Populate(awkward-headers)
  add_subdirectory(${awkward-headers_SOURCE_DIR} ${awkward-headers_BINARY_DIR} EXCLUDE_FROM_ALL)
endif()

# Load interpreter & pybind11
find_package(Python COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG)

set(ICONV_FOUND FALSE)
if(ICONV_INCLUDE_DIRS AND ICONV_LIBRARIES)
    SET(ICONV_FOUND TRUE)
endif()

set (HEADERS
    kaitai/kaitaistream.h
    kaitai/kaitaistruct.h
    kaitai/exceptions.h
)

set (SOURCES
    kaitai/kaitaistream.cpp
)

set(STRING_ENCODING_TYPE "ICONV" CACHE STRING "Set the way strings have to be encoded (ICONV|NONE|...)")

set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

add_library (${PROJECT_NAME} SHARED ${HEADERS} ${SOURCES})
set_property(TARGET ${PROJECT_NAME} PROPERTY PUBLIC_HEADER ${HEADERS})

if (ZLIB_FOUND)
    target_include_directories(${PROJECT_NAME} PRIVATE ${ZLIB_INCLUDE_DIRS})
    target_link_libraries(${PROJECT_NAME} PRIVATE ${ZLIB_LIBRARIES})
    target_compile_definitions(${PROJECT_NAME} PRIVATE -DKS_ZLIB)
endif()

if(ICONV_FOUND)
    target_include_directories(${PROJECT_NAME} PRIVATE ${ICONV_INCLUDE_DIRS})
    target_link_libraries(${PROJECT_NAME} PRIVATE ${ICONV_LIBRARIES})
endif()

if (STRING_ENCODING_TYPE STREQUAL "ICONV")
    target_compile_definitions(${PROJECT_NAME} PRIVATE -DKS_STR_ENCODING_ICONV)
elseif (STRING_ENCODING_TYPE STREQUAL "NONE")
    target_compile_definitions(${PROJECT_NAME} PRIVATE -DKS_STR_ENCODING_NONE)
else()
    # User action requested
endif()

install(TARGETS ${PROJECT_NAME}
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
    PUBLIC_HEADER DESTINATION include/kaitai
)
