import sys
sys.path.append("..")
sys.path.append("build/Release")

from nodepasta.nodegraph import NodeGraph
from examples.example_nodes import const_source, output_node

import ImPasta

nodeTypes = [
    const_source.ConstSource,
    output_node.OutputNode
]

ng = NodeGraph()
for t in nodeTypes:
    print(f"Registering {t.NODETYPE}")
    ng.registerNodeClass(t)

src = ng.addNode(const_source.ConstSource)
out = ng.addNode(output_node.OutputNode)
ng.makeLink(src.outputs[0], out.inputs[0])

src.pos.x = 200
out.pos.y = 50

gui = ImPasta.ImPastaGUI(ng)  # type: ignore
gui.run()
gui.stop()
