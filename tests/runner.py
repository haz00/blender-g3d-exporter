import logging
import sys
import unittest
from pathlib import Path


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)-20s %(levelname)8s %(name)25s  %(message)s')

    sys.path.append(str(Path(__file__).parents[1]))
    import tests

    classes = [
        tests.base.BaseTest,
        tests.builder_test.G3dBuilderTest,
        tests.builder_test.MeshNodeDataBuilderTest,
        tests.builder_test.BlendweightAttributeBuilderTest,
    ]

    suite = unittest.TestSuite()

    for cls in classes:
        suite.addTest(unittest.makeSuite(cls))

    result = unittest.TextTestRunner().run(suite).wasSuccessful()
    sys.exit(not result)


if __name__ == '__main__':
    main()