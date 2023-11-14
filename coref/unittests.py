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
# version 1.6 as of 2nd June 2023

import glob
import json
import os
import shutil
import tempfile

import git
import pytest
from corefserver import CorefServer

# run (pytest-6.2.3)
#   pytest coref/unittests.py -vv -s
#  -s shows print statements in test
#  -k test_edit_modliteral (filters tests which do not match argument)

# see: https://flask.palletsprojects.com/en/2.1.x/testing/
#      https://stackoverflow.com/questions/17801300/how-to-run-a-method-before-all-tests-in-all-classes

PATH = "coref"


# launched only once
@pytest.fixture(scope="session")
def app():
    #app = create_app()
    #app.config.update({
    #    "TESTING": True,
    #})
    #print("zzzzzzzzzzzzzzzzzzzz")
    aes = CorefServer(4569,
                      [PATH + "/pp_001.xml", PATH + "/wikipedia.shakespeare.xml", PATH + "/wikipedia.welsh.xml"],
                      [PATH + "/pp.amr.txt", PATH + "/shakespeare.amr.txt", PATH + "/welsh.amr.txt"],
                      )
    app = aes.app

    # other setup can go here

    yield app
    # clean up / reset resources here


# start server just for one test without any validating stuff to test git
@pytest.fixture()
def app_git():
    datadir = tempfile.TemporaryDirectory()
    print("temporary test directory", datadir)
    shutil.copyfile(PATH + "/pp_001.xml", datadir.name + "/pp_001.xml")
    shutil.copyfile(PATH + "/pp.amr.txt", datadir.name + "/pp.amr.txt")
    repo = git.Repo.init(datadir.name)
    repo.git.add(datadir.name + "/pp_001.xml")
    repo.git.add(datadir.name + "/pp.amr.txt")
    repo.git.commit("-m", "initial")

    aes = CorefServer(4569,
                      [datadir.name + "/pp_001.xml"],
                      [datadir.name + "/pp.amr.txt"],
                      )
    app = aes.app

    # other setup can go here

    yield app, repo
    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def client_git(app_git):
    app, repo = app_git
    #return app_git.test_client()
    return app.test_client(), repo


def test_request_example(client):
    response = client.get("/")
    #print("res", response.data, file=sys.stderr)
    assert b"<!DOCTYPE html>\n<html>\n\n<head>" in response.data


def test_info(client):
    response = client.get("/version")
    res = json.loads(response.data)
    assert res == {'name': 'AMR Coreference Editor', 'version': '1.6', 'apiversion': 1.1}

    response = client.get("/info")
    res = json.loads(response.data)
    assert sorted(res.keys()) == ['apiversion', 'cmdline', 'hostname', 'pwd', 'version']


def test_read(client):
    response = client.get("/read", query_string={"num": 1})
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert len(res["svgdict"]) == 19
    assert "lpp_1943.6" in res["svgdict"]
    assert res['filename'] == PATH + '/pp_001.xml'

    assert len(res["chaintable"]) == 9
    assert len(res["chaintable"]["0"]) == 10
    assert res["chaintable"]["0"][0] == "<span class=\"chain\" data=\"G_1_i\" style=\"background-color:#fff6b6;color:black\"><b>2</b>: i / i</span>"

    assert res["bridgingtable"]["10"][0] == '<span class="bridgingtype">Superset: <span class="chain" data="G_4_b" style="background-color:#ffeccc;color:black"><b>5</b>: b / boa</span> <span class="chain" data="G_5_t" style="background-color:#ffeccc;color:black"><b>6</b>: t / they</span> <span class="chain" data="G_16_b2" style="background-color:#ffeccc;color:black"><b>17</b>: b2 / boa</span></span><br>members: '


def test_read_badnum(client):
    response = client.get("/read", query_string={"num": 4})
    res = json.loads(response.data)
    #print("res", res)
    assert res['error'] == 'invalid sentence number: must be between 1 and 3\n'


def test_read_next(client):
    response = client.get("/next", query_string={"num": 1,
                                                 "direction": "next"})
    res = json.loads(response.data)
    #print("res", res["numsent"], res["num"])
    assert res["num"] == 2


def test_read_prec(client):
    response = client.get("/next", query_string={"num": 3,
                                                 "direction": "preceding"})
    res = json.loads(response.data)
    #print("res", res["numsent"], res["num"])
    assert res["num"] == 2


def test_read_window(client):
    response = client.get("/read", query_string={"num": 1,
                                                 "showfrom": 3,
                                                 "shownumber": 2})
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert len(res["svgdict"]) == 2
    assert "lpp_1943.3" in list(res["svgdict"].keys())[0]

    assert res["svgdict"]["lpp_1943.3"]["svg"].startswith("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n")


def test_add_new_chain(client):
    response = client.get("/addtochain", query_string={"num": 1,
                                                       "showfrom": 3,
                                                       "shownumber": 2,
                                                       "from": "G_2_a",
                                                       "to": "G_3_t2"})
    print("res", response.data)
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 10
    assert res["chaintable"]["9"][0] == "<span class=\"chain\" data=\"G_2_a\" style=\"background-color:#ff7900;color:black\"><b>3</b>: a / animal</span>"


def test_add_new_chain_badnum(client):
    response = client.get("/addtochain", query_string={"num": 0,
                                                       "showfrom": 3,
                                                       "shownumber": 2,
                                                       "from": "G_2_a",
                                                       "to": "G_3_t2"})
    #print("res", response.data)
    res = json.loads(response.data)
    assert res["error"] == "invalid sentence number: must be between 1 and 3\n"


def test_delete_chain(client):
    response = client.get("/addtochain", query_string={"num": 1,
                                                       "showfrom": 3,
                                                       "shownumber": 2,
                                                       "from": "G_2_a",
                                                       "to": "G_2_a"})
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 9


def test_add_to_chain(client):
    response = client.get("/addtochain", query_string={"num": 1,
                                                       "showfrom": 3,
                                                       "shownumber": 2,
                                                       "from": "G_14_p2",
                                                       "to": "G_2_a"})
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 9
    assert len(res["chaintable"]["6"]) == 4
    #assert res["chaintable"]["8"][0] == "<span class=\"chain\" data=\"G_2_a\" style=\"background-color:#ff8ad4;color:black\"><b>3</b> a / animal</span>"


def test_remove_from_chain(client):
    response = client.get("/addtochain", query_string={"num": 1,
                                                       "showfrom": 3,
                                                       "shownumber": 2,
                                                       "from": "G_2_a",
                                                       "to": "G_2_a"})
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 9
    assert len(res["chaintable"]["6"]) == 3


def ls(dn):
    for x in glob.glob(dn + "/*"):
        print("%-50s\t%7d" % (x, os.path.getsize(x)))


# test whether server stops if backup file exists
def test_nogit_back_exists():
    datadir = tempfile.TemporaryDirectory()
    print("temporary test directory", datadir)
    shutil.copyfile(PATH + "/pp_001.xml", datadir.name + "/pp_001.xml")
    shutil.copyfile(PATH + "/pp_001.xml", datadir.name + "/pp_001.xml.2")
    shutil.copyfile(PATH + "/pp_001.xml", datadir.name + "/pp_002.xml")
    shutil.copyfile(PATH + "/pp_001.xml", datadir.name + "/pp_002.xml.2")
    shutil.copyfile(PATH + "/pp.amr.txt", datadir.name + "/pp.amr.txt")

    ls(datadir.name)

    # should crahs here, since we are in no-git mode and the backup file is already there
    try:
        CorefServer(4569,
                    [datadir.name + "/pp_001.xml", datadir.name + "/pp_002.xml"],
                    [datadir.name + "/pp.amr.txt"],
                    )

    except Exception as e:
        assert str(e) == "Edited file(s) <%s/pp_001.xml, %s/pp_002.xml> not under git version control. Backup file(s) <%s/pp_001.xml.2, %s/pp_002.xml.2> exists already.\nPlease rename Backup file first" % (datadir.name, datadir.name, datadir.name, datadir.name)


# test git add/commit
def test_edit_addinstance_git(client_git):
    client, repo = client_git

    response = client.get("/addtochain", query_string={"num": 1,
                                                       "showfrom": 3,
                                                       "shownumber": 2,
                                                       "from": "G_14_p2",
                                                       "to": "G_2_a"})
    ls(repo.working_dir)
    res = json.loads(response.data)
    assert len(res["chaintable"]) == 9
    assert len(res["chaintable"]["6"]) == 4

    response = client.get("/save", query_string={"num": 1})
    #res = json.loads(response.data)
    #print(res)
    for m in repo.head.log():
        print(m)
    assert "commit: metamorphosed coref editor: 1 files saved" in repo.head.log()[-1].message
