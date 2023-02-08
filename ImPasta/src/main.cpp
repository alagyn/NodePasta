#include <boost/bind/bind.hpp>
#include <gui_utils.h>
#include <iostream>
#include <test.h>

using namespace BDD;

int main(int argc, char** argv)
{
    std::cout << "Init GUI\n";
    if(!gui_init())
    {
        exit(1);
    }
    std::cout << "Init Node Editor\n";
    NodeEditorInitialize();

    std::cout << "Run\n";
    gui_run(boost::bind(NodeEditorShow));

    std::cout << "Shutdown Editor\n";
    //NodeEditorShutdown();
    std::cout << "Stop GUI\n";
    gui_stop();
}