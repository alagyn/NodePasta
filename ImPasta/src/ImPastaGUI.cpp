
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

            ImNodes::PushAttributeFlag(ImNodesAttributeFlags_EnableLinkDetachWithDragClick);

            ImNodesIO& io = ImNodes::GetIO();
            io.LinkDetachWithModifierClick.Modifier = &ImGui::GetIO().KeyCtrl;
            io.MultipleSelectModifier.Modifier = &ImGui::GetIO().KeyCtrl;
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
                nodeGraph.makeLink(startPort, endPort);
            }

            int linkID;
            if(ImNodes::IsLinkDestroyed(&linkID))
            {
                nodeGraph.remLink(linkID);
            }

            ImGui::End();
        }

        void renderNode(py::object node)
        {
            int id = py::extract<int>(node.attr("nodeID"));
            // Set node pos
            py::object pos = node.attr("pos");
            if(!ImNodes::IsNodeSelected(id))
            {
                ImNodes::SetNodeGridSpacePos(
                    id, ImVec2(py::extract<float>(pos.attr("x")), py::extract<float>(pos.attr("y"))));
            }
            else
            {
                ImVec2 imPos = ImNodes::GetNodeGridSpacePos(id);
                pos.attr("x") = imPos.x;
                pos.attr("y") = imPos.y;
            }

            // build node
            ImNodes::BeginNode(id);

            std::string name = py::extract<std::string>(node.attr("NODETYPE"));
            ImNodes::BeginNodeTitleBar();
            ImGui::TextUnformatted(name.c_str());
            ImNodes::EndNodeTitleBar();

            // build input ports
            {
                py::stl_input_iterator<py::object> iter(node.attr("inputs")), end;
                for(; iter != end; ++iter)
                {
                    py::object port = *iter;
                    if(py::extract<bool>(port.attr("port").attr("variable")))
                    {
                        // TODO render var ports
                        ImGui::Text("VarPort");
                    }
                    else
                    {
                        ImNodes::BeginInputAttribute(py::extract<int>(port.attr("portID")));
                        renderPort(port);
                        ImNodes::EndInputAttribute();
                    }
                    ImGui::Dummy(ImVec2(100, 5));
                }
            }

            // build output ports
            {
                py::stl_input_iterator<py::object> iter(node.attr("outputs")), end;
                for(; iter != end; ++iter)
                {
                    py::object port = *iter;
                    if(py::extract<bool>(port.attr("port").attr("variable")))
                    {
                        // TODO render var ports
                        ImGui::Text("VarPort");
                    }
                    else
                    {
                        ImNodes::BeginOutputAttribute(py::extract<int>(port.attr("portID")));
                        renderPort(port);
                        ImNodes::EndOutputAttribute();
                    }
                    ImGui::Dummy(ImVec2(100, 5));
                }
            }

            ImNodes::EndNode();

            // build links
            {
                py::stl_input_iterator<py::object> iter(node), end;
                for(; iter != end; ++iter)
                {
                    py::object link = *iter;
                    int linkID = py::extract<int>(link.attr("linkID"));
                    int parentPortID = py::extract<int>(link.attr("pPort").attr("portID"));
                    int childPortID = py::extract<int>(link.attr("cPort").attr("portID"));
                    ImNodes::Link(linkID, parentPortID, childPortID);
                }
            }
        }

        void renderPort(py::object port)
        {
            std::string name = py::extract<std::string>(port.attr("port").attr("name"));
            ImGui::Text(name.c_str());
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