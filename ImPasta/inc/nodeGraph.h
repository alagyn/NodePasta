#pragma once

#include <boost/python.hpp>

namespace py = boost::python;

namespace BDD {
    class NodeGraph
    {
    public:
        py::object graph;
        NodeGraph(py::object);

        py::object getLink(int parentPortID, int childPortID);
        void makeLink(int parentPortID, int childPortID);
        void remLink(int linkID);
    };
} //namespace BDD