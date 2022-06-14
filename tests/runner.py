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
        tests.builder_test.G3dBuilderTest,
        tests.builder_test.MeshNodeDataBuilderTest,
        tests.builder_test.BlendweightAttributeBuilderTest,
    ]

    # read the cli args that were passed after --
    names = sys.argv[sys.argv.index("--") + 1:]

    if not names:
        from tests.common import qualified_classname
        names = [qualified_classname(cls) for cls in classes]

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(names)

    result = unittest.TextTestRunner().run(suite).wasSuccessful()
    sys.exit(not result)


if __name__ == '__main__':
    main()