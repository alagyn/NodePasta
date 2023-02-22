#include <nodeGraph.h>

namespace BDD {
    NodeGraph::NodeGraph(py::object ng)
        : graph(ng)
    {
    }

    py::object NodeGraph::getLink(int parentPortID, int childPortID)
    {
        return graph.attr("getLinkByPortID")(parentPortID, childPortID);
    }

    void NodeGraph::makeLink(int parentPortID, int childPortID)
    {
        graph.attr("makeLinkByID")(parentPortID, childPortID);
    }

    void NodeGraph::remLink(int linkID)
    {
        graph.attr("unlinkByID")(linkID);
    }
} //namespace BDD