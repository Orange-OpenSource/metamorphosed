#!/usr/bin/env python3

import os
import sys

mydir = os.path.normpath(os.path.dirname(__file__))
print("the file has been renamed, please run:")
print("  %s/metamorphosed_server.py %s\n" % (mydir, " ".join(sys.argv[1:])))
