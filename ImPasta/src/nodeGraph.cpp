#include <nodeGraph.h>

namespace BDD {
    NodeGraph::NodeGraph(py::object ng)
        : graph(ng)
    {
    }
} //namespace BDD