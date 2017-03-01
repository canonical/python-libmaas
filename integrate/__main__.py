import sys

import testtools.run


argv = sys.argv[0], "discover", "integrate", *sys.argv[1:]
testtools.run.main(argv, sys.stdout)
