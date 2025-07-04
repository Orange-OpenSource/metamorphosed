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
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke

# run (pytest-6.2.3)
#   pytest unittests_gui.py -vv
#  -s shows print statements in test
#  -k test_edit_modliteral (filters tests which do not match argument)

import os
import pytest
import shutil
import tempfile
import time
from threading import Thread

import metamorphosed.selenium_test as selenium_test
import metamorphosed.amrdoc as amrdoc
from metamorphosed.server import AMR_Edit_Server


PORT = 4568

mydir = os.path.dirname(__file__)


# launched only once
@pytest.fixture(scope="session")
def app2():
    datadir = tempfile.TemporaryDirectory()
    print("temporary test directory", datadir)
    shutil.copyfile(os.path.join(mydir, "metamorphosed/data/testamr.txt"),
                    os.path.join(datadir.name, "testamr.txt"))

    aes = AMR_Edit_Server(PORT,
                          datadir.name + "/testamr.txt",
                          None,
                          None,
                          None,
                          None,
                          False
                          )
    app = aes.app
    thread = Thread(target=app.run, daemon=True, kwargs=dict(host='localhost', port=PORT))
    thread.start()
    time.sleep(5)

    # other setup can go here

    yield app, datadir


@pytest.fixture()
def client(app2):
    app, datadir = app2
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
    gt = selenium_test.GUITest(port=PORT, browser="chrome", headless=True)
    gt.runtests()

    # copy result to metamorphosed dir to be able to compare manually
    shutil.copyfile(os.path.join(datadir.name, "testamr.txt.2"), os.path.join(mydir, "tmp-ui-test-results.txt"))

    res = getcontents(os.path.join(datadir.name, "testamr.txt.2"), "::save-date")

    ref = getcontents(os.path.join(mydir, "metamorphosed/data/ui-test-results.txt"), "::save-date")
#    ofp = open('ref', 'w')
#    print(ref, file=ofp)
#    ofp.close()
#    ofp = open('res', 'w')
#    print(res, file=ofp)
#    ofp.close()

    assert ref == res
