#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2022-2024,  Orange
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of Orange nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL ORANGE BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke

import argparse
import os
import sys

from metamorphosed import AMR_Edit_Server

mydir = os.path.dirname(__file__)


def main():
    parser = argparse.ArgumentParser("metAMoRphosED: the Abstract Meaning Representation Editor")

    parser.add_argument("--port", "-p", default=4567, type=int, help="port to use")
    parser.add_argument("--file", "-f", required=True, help="AMR file to edit")
    parser.add_argument("--compare", nargs="+", help="AMR file of additional annotators to compare with file given by --file")
    parser.add_argument("--author", help="author (for git), use format 'Name <mail@example.com>', if absent current user+mail is used")
    parser.add_argument("--relations", "-R", default=mydir + "/data/relations.txt", help="list of valid AMR-relations (simple text file with list of all valid relations)")
    parser.add_argument("--relationsdoc", default=mydir + "/data/relations-doc.json", help="examples for valid AMR-relations (json file)")
    parser.add_argument("--concepts", "-C", default=None, help="list of valid AMR-concepts (simple text file with list of all valid concepts)")
    parser.add_argument("--pbframes", "-P", default=None, help="Propbank frameset documentation (directory with xml files)")
    parser.add_argument("--constraints", "-c", default=None, help="constraints for subjects and predicates (yaml file)")
    parser.add_argument("--readonly", "--ro", default=False, action="store_true", help='browse corpus only')
    parser.add_argument("--reifications", "-X", default=mydir + "/data/reification-table.txt", help="table for (de)reification")
    parser.add_argument("--nogit", dest="git", default=True, action="store_false", help='no git add/commit, even if file is git controlled (does nevertheless overwrite existing file)')
    parser.add_argument("--override", default=False, action="store_true", help='if file is not under git control, override existing backup file')
    parser.add_argument("--edge_predictor", "-E", default=None, help="yml file which defines an Edge Predictor class (filename, Classname and parameters")
    parser.add_argument("--smatchpp", "-S", action='store_true', help='use smatchpp (https://github.com/flipz357/smatchpp) instead of smatch')
    parser.add_argument("--preferred", default=None, help="json file with preferred graphs (used together which --compare)")
    parser.add_argument("--umr", action='store_true', help='inpput file is in UMR format')
    parser.add_argument("--dockerargs", nargs="+", default=None, help=argparse.SUPPRESS) # only used in the docker image entrypoint
    # format: datadir file [compare1 compare2 ...]

    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()
        try:
            amrfile = args.file
            compare = args.compare
            if args.dockerargs:
                datadir = args.dockerargs[0]
                amrfile = os.path.join(datadir, args.dockerargs[1])
                if len(args.dockerargs) > 2:
                    compare = []
                    for cf in args.dockerargs[2:]:
                        compare.append(os.path.join(datadir, cf))

            aes = AMR_Edit_Server(args.port, amrfile, args.pbframes,
                                  args.relations,
                                  args.concepts,
                                  args.constraints, args.readonly,
                                  author=args.author,
                                  reifications=args.reifications,
                                  relationsdoc=args.relationsdoc,
                                  predictor=args.edge_predictor,
                                  do_git=args.git,
                                  compare=compare,
                                  smatchpp=args.smatchpp,
                                  preferred=args.preferred,
                                  override=args.override,
                                  umr=args.umr)
            aes.start()
        except Exception as e:
            print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
