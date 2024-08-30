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
        time.sleep(5)

    def readsentence(self):
        read = self.driver.find_element(By.ID, "lire")
        read.click()
        print("sentence read")

    def addconcept(self):
        # add concept
        field = self.driver.find_element(By.ID, "concept")
        field.clear()
        field.send_keys("house" + Keys.RETURN)

        time.sleep(2)
        print("concept 'house' added")

    def addname(self):
        # add name
        var = self.driver.find_element(By.ID, 'nameof')
        s = Select(var)
        s.select_by_value("h")
        field = self.driver.find_element(By.ID, "name")
        field.clear()
        field.send_keys("Tir na nOg")
        button = self.driver.find_element(By.ID, "addname")
        button.click()
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
        #b.click()
        time.sleep(2)

        b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="node#h#house"]')))
        ac.move_to_element_with_offset(b, 0, 20).click().perform()
        #b.click()
        print("concept linked")
        time.sleep(1)

    def settop(self):
        # set new top
        var = self.driver.find_element(By.ID, 'topnode')
        s = Select(var)
        s.select_by_value("h")
        button = self.driver.find_element(By.ID, "settop")
        button.click()

    def modstart(self):
        # change starting point of edge
        # edge
        b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="edge#p#n#:name"]')))
        #b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text()="????"]')))
        #ac = ActionChains(self.driver)
        #ac.move_to_element_with_offset(b, 0, 5).click().perform()
        b.click()
        time.sleep(2)

        # new start
        b = self.wait.until(EC.element_to_be_clickable((By.ID, 'node#b#bear-02')))
        #ac = ActionChains(self.driver)
        #ac.move_to_element_with_offset(b, 0, 5).click().perform()
        b.click()

        time.sleep(2)

    def addliteral(self):
        # add literal
        var = self.driver.find_element(By.ID, 'literalof')
        s = Select(var)
        s.select_by_value("s")

        field = self.driver.find_element(By.ID, "relationforliteral")
        field.clear()
        field.send_keys("quant")

        field = self.driver.find_element(By.ID, "newliteral")
        field.clear()
        field.send_keys("245.6")

        button = self.driver.find_element(By.ID, "addliteral")
        button.click()

        time.sleep(2)

    def safe(self):
        # safefile
        x = self.driver.find_element(By.ID, "save")
        x.click()
        print("file saved")
        time.sleep(2)

    def runtests(self):
        self.readsentence()
        self.addconcept()
        self.addname()
        self.linkconcept()
        self.settop()
        self.modstart()
        self.addliteral()
        self.safe()


if __name__ == "__main__":
    input("start metamorphosed on port %d and enter to continue... " % 4567)

    gt = GUITest()
    gt.runtests()

    input("hit enter to terminate> ")
