#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2022-2023,  Orange
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
# Software Name: MetAMoRphosED AMR-Editor for coreferences
# Author: Johannes Heinecke
# version 1.2 as of 2nd June 2023

import sys
import pytest
import json
import time

from corefserver import CorefServer


# run (pytest-6.2.3)
#   pytest unittests.py -vv -s
#  -s shows print statements in test
#  -k test_edit_modliteral (filters tests which do not match argument)

# see: https://flask.palletsprojects.com/en/2.1.x/testing/
#      https://stackoverflow.com/questions/17801300/how-to-run-a-method-before-all-tests-in-all-classes

# launched only once
@pytest.fixture(scope="session")
def app():
    #app = create_app()
    #app.config.update({
    #    "TESTING": True,
    #})
    #print("zzzzzzzzzzzzzzzzzzzz")
    aes = CorefServer(4569,
                      ["pp_001.xml"],
                      ["pp.amr.txt"],
                      )
    app = aes.app
    

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()



def test_request_example(client):
    response = client.get("/")
    #print("res", response.data, file=sys.stderr)
    assert b"<!DOCTYPE html>\n<html>\n\n<head>" in response.data



def test_read(client):
    response = client.get("/read", query_string = {"num": 1})
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert len(res["svgdict"]) == 19
    assert "lpp_1943.6" in res["svgdict"]
    assert res['filename'] == 'pp_001.xml'

    assert len(res["chaintable"]) == 8
    assert len(res["chaintable"]["0"]) == 10
    assert res["chaintable"]["0"][0] == "<span class=\"chain\" data=\"G_1_i\" style=\"background-color:#fff6b6;color:black\"><b>2</b>: i / i</span>"

    assert res["bridgingtable"]["9"][0] == '<span class="bridgingtype">Superset: <span class="chain" data="G_4_b" style="background-color:#ffeccc;color:black"><b>5</b>: b / boa</span> <span class="chain" data="G_5_t" style="background-color:#ffeccc;color:black"><b>6</b>: t / they</span></span><br>members: '


def test_read_window(client):
    response = client.get("/read", query_string = {"num": 1,
                                                   "showfrom": 3,
                                                   "shownumber": 2})
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert len(res["svgdict"]) == 2
    assert "lpp_1943.3" in list(res["svgdict"].keys())[0]

    assert res["svgdict"]["lpp_1943.3"]["svg"].startswith("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n")


def test_add_new_chain(client):
    response = client.get("/addtochain", query_string = {"num": 0,
                                                         "showfrom": 3,
                                                         "shownumber": 2,
                                                         "from": "G_2_a",
                                                         "to": "G_3_t2"})
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 9
    assert res["chaintable"]["8"][0] == "<span class=\"chain\" data=\"G_2_a\" style=\"background-color:#ff8ad4;color:black\"><b>3</b>: a / animal</span>"

def test_delete_chain(client):
    response = client.get("/addtochain", query_string = {"num": 0,
                                                         "showfrom": 3,
                                                         "shownumber": 2,
                                                         "from": "G_2_a",
                                                         "to": "G_2_a"})
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 8

def test_add_to_chain(client):
    response = client.get("/addtochain", query_string = {"num": 0,
                                                         "showfrom": 3,
                                                         "shownumber": 2,
                                                         "from": "G_14_p2",
                                                         "to": "G_2_a"})
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 8
    assert len(res["chaintable"]["6"]) == 4
    #assert res["chaintable"]["8"][0] == "<span class=\"chain\" data=\"G_2_a\" style=\"background-color:#ff8ad4;color:black\"><b>3</b> a / animal</span>"


def test_remove_from_chain(client):
    response = client.get("/addtochain", query_string = {"num": 0,
                                                         "showfrom": 3,
                                                         "shownumber": 2,
                                                         "from": "G_2_a",
                                                         "to": "G_2_a"})
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 8
    assert len(res["chaintable"]["6"]) == 3
