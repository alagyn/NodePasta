
from example_nodes import const_source, nullable_input, output_node, sum_node
from node_graph import NodeGraph

if __name__ == '__main__':
    ng = NodeGraph()

    src1 = const_source.ConstSource(10)
    src2 = const_source.ConstSource(2)

    ng.addNodes(src1, src2)

    p = nullable_input.Power()
    s = sum_node.SumNode()
    o = output_node.OutputNode()

    ng.addNodes(p, s, o)

    src1.addChild(p, src1.o.value, p.i.base)
    src2.addChild(p, src2.o.value, p.i.power)

    p.addChild(s, p.o.value, s.i.a)
    src2.addChild(s, src2.o.value, s.i.b)

    s.addChild(o, s.o.value, o.i.value)

    ng.execute()