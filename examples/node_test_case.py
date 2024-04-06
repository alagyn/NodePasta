from .example_nodes.offset_node import OffsetNode
from .example_nodes.sum_list import SumListNode

from nodepasta.testing.tester import Tester

# Ideally you would incorporate this into a real unittest framework


def test1():
    # Create test node
    node = OffsetNode()
    # Wrap in tester
    tester = Tester(node)

    node.init()
    node.args['offset'].value = 3
    node.setup()

    # (Input, Expected)
    values = [(1, 4), (2, 5), (-1, 2)]

    fail = False
    for i, x in values:
        # keys are the input name
        inputs = {
            "value": i
        }

        outputs = tester.test(inputs)

        # keys are the output name
        output = outputs["output"]
        if output != x:
            print(f"{output} != {x}")
            fail = True

    if not fail:
        print("Test 1 Passed")


def test2():
    # This shows how to test var ports
    node = SumListNode()
    tester = Tester(node)

    node.init()
    node.setup()

    inputs = {
        # var input is just a list
        "Inputs": [0, 1, 2, 3]
    }

    outputs = tester.test(inputs)
    output = outputs["Output"]
    if output != 6:
        print(f'{output} != 6')
    else:
        print("Test 2 Passed")


def main():
    test1()
    test2()


if __name__ == '__main__':
    main()
