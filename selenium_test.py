#!/usr/bin/env python3

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.firefox.service import Service
#from selenium.webdriver.common.actions import Actions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GUITest:
    def __init__(self, host="localhost", port=4567):
        # self.driverService = Service('/snap/bin/geckodriver')
        # self.driver = webdriver.Firefox(service=driverService)
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-search-engine-choice-screen")
        options.add_argument("--window-size=1420,900")
        self.driver = webdriver.Chrome(options=options)
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
        field.send_keys("house"+ Keys.RETURN)

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
        
        ActionChains(self.driver).scroll_by_amount(1000, 1000).perform()
        print("scrolled")

    def linkconcept(self):
        # only works with Chrome
        b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="node#l#live-01"]')))
        b.click()
        time.sleep(2)

        b = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="node#h#house"]')))
        b.click()
        print("concept linked")

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
        b.click()
        time.sleep(2)

        # new start
        b = self.wait.until(EC.element_to_be_clickable((By.ID, 'node#b#bear-02')))
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
    gt = GUITest()
    gt.runtests()

    input("hit enter to terminate> ")
