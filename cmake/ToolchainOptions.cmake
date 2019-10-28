
# LLVM related package
find_package(LLVM REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
list(APPEND CMAKE_MODULE_PATH "${LLVM_CMAKE_DIR}")

include(AddLLVM)

# Clang related package
find_package(Clang REQUIRED CONFIG)

# Compile flags
function(default_compile_options target)
  cmake_parse_arguments(ARG "" "" "PRIVATE_FLAGS;PUBLIC_FLAGS" ${ARGN})

  target_compile_options(${target} PRIVATE
    -Wall -Wextra -pedantic -Wunreachable-code -Wwrite-strings
    -Wpointer-arith -Wcast-align -Wcast-qual
    -Werror
  )

if(ARG_PRIVATE_FLAGS)
  target_compile_options(${target} PRIVATE
    "${ARG_PRIVATE_FLAGS}"
  )
endif()

if(ARG_PUBLIC_FLAGS)
  target_compile_options(${target} PUBLIC
    "${ARG_PUBLIC_FLAGS}"
  )
endif()
endfunction()


# Clang tidy
find_program(CLANG_TIDY
  NAMES clang-tidy clang-tidy-8 clang-tidy-7 clang-tidy-6.0
)

function(register_to_clang_tidy target)
  set_target_properties(${target}
    PROPERTIES
      CXX_CLANG_TIDY ${CLANG_TIDY}
  )
endfunction()

function(make_llvm_module name sources)
cmake_parse_arguments(ARG "" "" "INCLUDE_DIRS;DEPENDS;LINK_LIBS" ${ARGN})

add_llvm_library(${name}
  MODULE  ${LIB_SOURCES}
)

# Maybe this needs to be "LLVM_MAIN_INCLUDE_DIRS"
target_include_directories(${name}
  SYSTEM
  PUBLIC
  ${LLVM_INCLUDE_DIRS}
)

if(ARG_INCLUDE_DIRS)
  target_include_directories(${name}
    PRIVATE
    ${ARG_INCLUDE_DIRS}
  )
endif()

target_compile_definitions(${name}
  PRIVATE
  ${LLVM_DEFINITIONS}
)

register_to_clang_tidy(${name}
  ${INSTRUMENTATIONLIB_SOURCES}
)

endfunction()
