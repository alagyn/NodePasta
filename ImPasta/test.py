import sys
sys.path.append("..")
sys.path.append("C:/Users/benki/Home/libs/boost_1_81_0/stage/lib")
sys.path.append("build/Release")

from nodepasta.nodegraph import NodeGraph
from nodepasta.node import LinkAddr
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

src1 = const_source.ConstSource()
outN = output_node.OutputNode()

ng.addNode(src1)
ng.addNode(outN)
ng.makeLink(src1, outN, LinkAddr(0, 0, 0, 0))

src1.pos.x = 200
outN.pos.y = 50

gui = ImPasta.ImPastaGUI(ng)
gui.init()
gui.run()
gui.stop()
