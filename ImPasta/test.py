import sys
sys.path.append("..")
sys.path.append("build/Release")

from nodepasta.nodegraph import NodeGraph
from nodepasta.utils import Vec
from examples.example_nodes import const_source, output_node, offset_node, listifier

import ImPasta

nodeTypes = [
    const_source.ConstSource,
    output_node.OutputNode,
    offset_node.OffsetNode,
    listifier.ListifierNode
]

ng = NodeGraph()
for t in nodeTypes:
    print(f"Registering {t.NODETYPE}")
    ng.registerNodeClass(t)

print("Adding nodes")
src = ng.addNode(const_source.ConstSource)
out = ng.addNode(output_node.OutputNode)
offset = ng.addNode(offset_node.OffsetNode)
listi = ng.addNode(listifier.ListifierNode)
# ng.makeLink(src.outputs[0], out.inputs[0])

src.pos.x = 50
offset.pos.x = 150
out.pos.x = 250
listi.pos = Vec(50, 100)


print("PY: Create GUI")
gui = ImPasta.ImPastaGUI(ng)  # type: ignore
print("PY: Init GUI")
gui.init()
print("PY: Run GUI")
gui.run()
print("PY: Stop GUI")
gui.stop()
