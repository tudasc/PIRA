set(PROJECT_NAME instrumentationlib)
set(TARGETS_EXPORT_NAME ${PROJECT_NAME}-target)


set(LIB_SOURCES
  src/InstrumentationLib.cpp
)

make_llvm_module(instrumentationlib
  "${LIB_SOURCES}"
  INCLUDE_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${PROJECT_SOURCE_DIR}/lib/include
)

install(
  TARGETS instrumentationlib 
  EXPORT ${TARGETS_EXPORT_NAME}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
)

install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake
  DESTINATION lib/cmake
)
