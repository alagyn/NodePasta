cmake_minimum_required(VERSION 3.25.2)

project(ImPasta)

add_subdirectory(third-party)

set(Boost_DEBUG OFF)

set(Boost_NO_BOOST_CMAKE ON)
set(Boost_NO_SYSTEM_PATHS TRUE)
set(Boost_USE_DEBUG ON)
set(Boost_USE_DEBUG_PYTHON ON)
set(Boost_USE_DEBUG_RUNTIME ON)
set(Boost_USE_STATIC_LIBS OFF)

set(BOOST_ROOT "C:/Users/benki/Home/libs/boost_1_81_0")
set(BOOST_LIBRARY_DIR "C:/Users/benki/Home/libs/boost_1_81_0/stage/lib")

find_package(Python3 3.11
    REQUIRED
    COMPONENTS Interpreter Development
)

find_package(Boost 1.81.0
    REQUIRED
    COMPONENTS system filesystem python311
)

set(${PROJECT_NAME}_SRCS
    src/ImPastaGUI.cpp
    src/nodeGraph.cpp
    src/gui_utils.cpp
    src/main.cpp
)

add_library(${PROJECT_NAME} MODULE ${${PROJECT_NAME}_SRCS})

target_link_libraries(
    ${PROJECT_NAME}
    PRIVATE
    Boost::system
    Boost::filesystem
    Boost::python311
    Python3::Python
    ImGUI
)

target_include_directories(${PROJECT_NAME}
    PRIVATE
    inc
)

set(TEST_SRCS
    src/gui_utils.cpp
    src/main.cpp
)

add_executable(TEST ${TEST_SRCS})
target_link_libraries(
    TEST
    PRIVATE
    Boost::system
    Boost::filesystem
    ImGUI
)

target_include_directories(TEST
    PRIVATE
    inc
)

set_target_properties(${PROJECT_NAME}
    PROPERTIES
    PREFIX ""
    OUTPUT_NAME "ImPasta"
)

if(WIN32)
    set_target_properties(${PROJECT_NAME}
        PROPERTIES
        SUFFIX ".pyd"
    )
endif()