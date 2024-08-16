import os
import pytest
import shutil
import tempfile
import time
from threading import Thread

import selenium_test

import amrdoc
from server import AMR_Edit_Server

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
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke

# run (pytest-6.2.3)
#   pytest unittests.py -vv -s
#  -s shows print statements in test
#  -k test_edit_modliteral (filters tests which do not match argument)


PORT=4568

# launched only once
@pytest.fixture(scope="session")
def app2():
    datadir = tempfile.TemporaryDirectory()
    print("temporary test directory", datadir)
    shutil.copyfile("testamr.txt", os.path.join(datadir.name, "testamr.txt"))

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


def test_gui(client):
    client, datadir = client
    gt = selenium_test.GUITest(port=PORT)
    gt.runtests()

    print("ZZZZ", datadir)
    #ifp = open(os.path.join(datadir.name, "testamr.txt.2"))
    #contents = ifp.read()
    #print("contents", contents)

    doc = amrdoc.AMRdoc(os.path.join(datadir.name, "testamr.txt.2"))
    result = doc.sentences[0].amr
    ref = '''(h / house
   :ARG0-of (l / live-01
               :snt2-of (m / multi-sentence
                           :snt1 (b / bear-02
                                    :ARG1 p
                                    :location c
                                    :name (n / name
                                             :op1 "Naomie"
                                             :op2 "Harris")))
               :ARG0 (p / person
                        :wiki "Q156586")
               :location (c / city
                            :name (n2 / name
                                      :op1 "London")
                            :wiki "Q84")
               :mod (s / still
                       :quant 245.6))
   :name (n1 / name
             :op1 "Tir"
             :op2 "na"
             :op3 "nOg"))'''
    # we did only modify the first sentence
    assert ref == result
