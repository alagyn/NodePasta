
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include <boost/python.hpp>
#include <imgui.h>
#include <imnodes.h>

#include <gui_utils.h>
#include <nodeGraph.h>

namespace py = boost::python;

namespace BDD {

    constexpr int windowFlags =
        ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse;

    class ImPastaGUI
    {
    private:
        NodeGraph nodeGraph;

    public:
        ImPastaGUI(py::object nodeGraph)
            : nodeGraph(nodeGraph)
        {
        }

        void init()
        {
            gui_init();
        }

        void stop()
        {
            gui_stop();
        }

        void run()
        {
            gui_run(boost::bind(&ImPastaGUI::render, this));
        }

        void render()
        {
            auto io = ImGui::GetIO();
            io.ConfigFlags &= ~ImGuiConfigFlags_NavEnableGamepad;

            ImGui::SetNextWindowPos(ImVec2(0, 0));
            ImGui::SetNextWindowSize(io.DisplaySize);

            ImGui::Begin("Nodepasta", nullptr, windowFlags);
            ImNodes::BeginNodeEditor();

            py::stl_input_iterator<py::object> iter(nodeGraph.graph), end;
            for(; iter != end; ++iter)
            {
                renderNode(*iter);
            }

            ImNodes::MiniMap(0.2f, ImNodesMiniMapLocation_TopRight);
            ImNodes::EndNodeEditor();

            // This has to happen after EndNodeEditor
            int startPort, endPort;
            if(ImNodes::IsLinkCreated(&startPort, &endPort))
            {
                // TODO
            }

            int linkID;
            if(ImNodes::IsLinkDestroyed(&linkID))
            {
                // TODO
            }

            ImGui::End();
        }

        void renderNode(py::object node)
        {
            int id = py::extract<int>(node.attr("nodeID"));
            // Set node pos
            py::object pos = node.attr("pos");
            ImNodes::SetNodeGridSpacePos(
                id, ImVec2(py::extract<float>(pos.attr("x")), py::extract<float>(pos.attr("y"))));

            // build node
            ImNodes::BeginNode(id);

            std::string name = py::extract<std::string>(node.attr("NODETYPE"));
            ImNodes::BeginNodeTitleBar();
            ImGui::TextUnformatted(name.c_str());
            ImNodes::EndNodeTitleBar();

            {
                // build ports
                py::stl_input_iterator<py::object> iter(node.attr("inputs")), end;
                for(; iter != end; ++iter)
                {
                    // TODO
                    //ImNodes::BeginInputAttribute();
                }
            }

            ImNodes::EndNode();

            {
                // build links
                py::stl_input_iterator<py::object> iter(node), end;
                for(; iter != end; ++iter)
                {
                    py::object link = *iter;
                    int linkID = py::extract<int>(link.attr("linkID"));
                    py::object addr = link.attr("addr");
                    //ImNodes::Link(linkID, 0, 1);
                    // TODO
                }
            }
        }
    };
} //namespace BDD

using namespace BDD;

BOOST_PYTHON_MODULE(ImPasta)
{
    py::class_<ImPastaGUI>("ImPastaGUI", py::init<py::object>("nodeGraph"))
        .def("init", &ImPastaGUI::init)
        .def("stop", &ImPastaGUI::stop)
        .def("run", &ImPastaGUI::run);
}