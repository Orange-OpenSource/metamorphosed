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
# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke

# tests GUI with Chrome
# TODO: largely perfectible, does not work on Firefox yet

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class GUITest:
    def __init__(self, host="localhost", port=4567, browser="chrome", headless=False):
        if browser == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-search-engine-choice-screen")
            if headless:
                options.add_argument("--headless=new")
            else:
                options.add_argument("--window-size=1420,900")
            self.driver = webdriver.Chrome(options=options)
        else:
            # not all tests working with firefox
            driverService = Service('/snap/bin/geckodriver')
            options = webdriver.firefox.options.Options()
            if headless:
                options.add_argument("-headless")
            self.driver = webdriver.Firefox(options=options, service=driverService)
        self.driver.get("http://%s:%d" % (host, port))
        self.wait = WebDriverWait(self.driver, 20)
        print("init OK")
        self.pause = 0.5
        time.sleep(5)

    def button(self, bid=None, xpath=None):
        if xpath:
            print("BUTTON", xpath)
            b = self.driver.find_element(By.XPATH, xpath)
        else:
            print("BUTTON", bid)
            b = self.driver.find_element(By.ID, bid)
        b.click()
        time.sleep(self.pause)
        return b

    def enter_text(self, bid, text, xpath=None):
        if xpath:
            print("TEXT", xpath, text)
            b = self.driver.find_element(By.XPATH, xpath)
        else:
            print("TEXT", bid, text)
            b = self.driver.find_element(By.ID, bid)
        b.clear()
        b.send_keys(text + Keys.RETURN)
        time.sleep(self.pause)

    def select(self, bid, index=None, value=None):
        print("SELECT", bid, index, value)
        b = self.driver.find_element(By.ID, bid)
        s = Select(b)
        if index:
            s.select_by_index(index)
        elif value:
            s.select_by_value(value)
        time.sleep(self.pause)

    def readsentence(self):
        #read = self.driver.find_element(By.ID, "lire")
        #read.click()
        self.button("lire")
        print("sentence read")

    def addconcept(self):
        # add concept
        self.enter_text("concept", "house")
        
        #time.sleep(2)
        print("concept 'house' added")

    def addname(self):
        # add name
        self.select("nameof", value="h")
        self.enter_text("name", "Tir na nOg")
        self.button("addname")

        print("named added")

        # not needed
        #ActionChains(self.driver).scroll_by_amount(1000, 1000).perform()
        #print("scrolled")

    def linkconcept(self):
        # only works with Chrome
        ActionChains(self.driver).scroll_by_amount(1000, 1000).perform()
        print("scrolled")

        b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="node#l#live-01"]')))
        ac = ActionChains(self.driver)
        ac.move_to_element_with_offset(b, 0, -20).click().perform()
        time.sleep(self.pause)

        b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="node#h#house"]')))
        ac.move_to_element_with_offset(b, 0, 20).click().perform()
        print("concept linked")
        time.sleep(self.pause)

    def settop(self):
        # set new top
        self.select("topnode", value="h")
        self.button("settop")

    def modstart(self):
        # change starting point of edge (n/name will moved from p/person to b/bear)
        # edge
        b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="edge#p#n#:name"]')))
        #b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text()="????"]')))
        #ac = ActionChains(self.driver)
        #ac.move_to_element_with_offset(b, 0, 5).click().perform()
        b.click()
        time.sleep(self.pause)

        # new start
        b = self.wait.until(EC.element_to_be_clickable((By.ID, 'node#b#bear-02')))
        #ac = ActionChains(self.driver)
        #ac.move_to_element_with_offset(b, 0, 5).click().perform()
        b.click()
        time.sleep(self.pause)

    def addliteral(self):
        # add literal
        self.select("literalof", value="s")
        self.enter_text("relationforliteral", "quant")
        self.enter_text("newliteral", "245.6")
        self.button("addliteral")

        time.sleep(self.pause)

    def addpartial(self):
        self.enter_text("sentnum", "2")
        self.button("addgraph")
        self.enter_text("addedgraph", "(x / kill :time (d / date-entity    :dayperiod (n / morning)))")
        self.enter_text("conceptmappings", "k/x")
        self.button("modifyaddgraph")
        print("graph added")
        #input("ENTER> ")

    def choosesentence(self):
        self.button("choosesentence")
        self.enter_text("textfilter", "the")
        self.button("modifysentencelist")
        self.select("sentencelist", index=3)
        #input("ENTER> ")
        
    def safe(self):
        # safefile
        self.button("save")
        print("file saved")


    def runtests(self):
        self.readsentence()
        self.addconcept()
        self.addname()
        self.linkconcept()
        self.settop()
        self.modstart()
        self.addliteral()
        self.addpartial()
        self.choosesentence()
        
        self.safe()


if __name__ == "__main__":
    input("start metamorphosed on port %d and enter to continue... " % 4567)

    gt = GUITest()
    gt.runtests()

    input("hit enter to terminate> ")
