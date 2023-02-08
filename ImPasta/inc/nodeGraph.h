#pragma once

#include <boost/python.hpp>

namespace py = boost::python;

namespace BDD {
    class NodeGraph
    {
    public:
        py::object graph;
        NodeGraph(py::object);
    };
} //namespace BDD