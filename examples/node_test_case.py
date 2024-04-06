from .example_nodes.offset_node import OffsetNode

from nodepasta.testing.tester import Tester

# Ideally you would incorporate this into a real unittest framework


def main():
    # Create test node
    node = OffsetNode()
    # Wrap in tester
    tester = Tester(node)

    node.init()
    node.args['offset'].value = 3
    node.setup()

    # (Input, Expected)
    values = [(1, 4), (2, 5), (-1, 2)]

    for i, x in values:
        # keys are the input name
        inputs = {
            "value": i
        }

        outputs = tester.test(inputs)

        # keys are the output name
        assert outputs["output"] == x


if __name__ == '__main__':
    main()
