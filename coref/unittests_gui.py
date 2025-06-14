#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2022-2025,  Orange
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

# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke

# run (pytest-6.2.3)
#   pytest coref/unittests_gui.py -vv
#  -s shows print statements in test
#  -k test_edit_modliteral (filters tests which do not match argument)

import os
import pytest
import shutil
import tempfile
import time
from threading import Thread

from corefserver import CorefServer
import selenium_coreftest

PATH = "coref"
PORT = 4569
mydir = os.path.dirname(__file__)


# start server just for one test without any validating stuff to test git
@pytest.fixture(scope="session")
def app():
    datadir = tempfile.TemporaryDirectory()
    print("temporary test directory", datadir)
    shutil.copyfile(PATH + "/pp_001.xml", datadir.name + "/pp_001.xml")
    shutil.copyfile(PATH + "/pp.amr.txt", datadir.name + "/pp.amr.txt")
    shutil.copyfile(PATH + "/wikipedia.welsh.xml", datadir.name + "/wikipedia.welsh.xml")
    shutil.copyfile(PATH + "/welsh.amr.txt", datadir.name + "/welsh.amr.txt")

    aes = CorefServer(PORT,
                      [datadir.name + "/pp_001.xml", datadir.name + "/wikipedia.welsh.xml"],
                      [datadir.name + "/pp.amr.txt", datadir.name + "/welsh.amr.txt"],
                      )
    app = aes.app
    thread = Thread(target=app.run, daemon=True, kwargs=dict(host='localhost', port=PORT))
    thread.start()
    time.sleep(2)

    # other setup can go here

    yield app, datadir

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    app, datadir = app
    return app.test_client(), datadir


def getcontents(fn, grep=None):
    with open(fn) as ifp:
        if not grep:
            return ifp.read()
        else:
            lines = []
            for line in ifp:
                if grep not in line:
                    lines.append(line)
            return "".join(lines)


def test_gui(client):
    client, datadir = client
    gt = selenium_coreftest.GUITest(port=PORT, browser="chrome", headless=True)
    gt.runtests()

    # copy result to metamorphosed dir to be able to compare manually
    shutil.copyfile(os.path.join(datadir.name, "wikipedia.welsh.xml.2"), os.path.join(mydir, "tmp-ui-coreftest-results.xml"))

    res = getcontents(os.path.join(datadir.name, "wikipedia.welsh.xml.2"), "::save-date")
    ref = getcontents(os.path.join(mydir, "ui-coreftest-results.xml"), "::save-date")
    ofp = open('ref', 'w')
    print(ref, file=ofp)
    ofp.close()
    ofp = open('res', 'w')
    print(res, file=ofp)
    ofp.close()

    assert ref == res
