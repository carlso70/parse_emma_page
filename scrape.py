from typing import Tuple, cast
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
import re
import pandas as pd
import os

# We use selenium to automate some web browser stuff that beautiful soup can't.
# That means we can click the javascript links on the website (ex: click accept terms and agreement stuff)


# DOWNLOAD THIS THING HERE https://github.com/mozilla/geckodriver/releases and save it on your comp


def element_exists_by_tag_name(driver, element) -> bool:
    try:
        driver.find_element_by_tag_name(element)
    except:
        return False
    return True


# returns a tuple (x,y,z). Displaying x to y of z results
def parse_result_count(display_results_string: str) -> tuple:
    # Need to replace the ',' in numbers > 999 to parse correctly
    x = int(display_results_string.split(" ")[1].replace(',', ''))
    y = int(display_results_string.split(" ")[3].replace(',', ''))
    z = int(display_results_string.split(" ")[5].replace(',', ''))
    return (x, y, z)


def accept_terms(driver) -> None:
    accept_button = driver.find_element_by_id(
        'ctl00_mainContentArea_disclaimerContent_yesButton')
    print("accept-button =>", accept_button)
    accept_button.click()


def get_links_to_issuer_homepage_details(driver) -> list:
    # get the details, this code pretty much the same as the issuers

    links_to_details = []
    while True:
        # find table on page and add links to each issuer
        table = driver.find_element_by_id('lvIssues')
        for row in table.find_elements_by_css_selector('tr'):
            for cell in row.find_elements_by_css_selector('td'):
                try:
                    link = cell.find_element_by_tag_name(
                        'a').get_attribute('href')
                    links_to_details.append(link)
                except NoSuchElementException:
                    pass

        # find next button
        next_button = driver.find_element_by_class_name('next')

        # Check if we can go to the next page or not
        attributes = next_button.get_attribute('class').split(" ")
        for attr in attributes:
            if attr == "disabled":
                return links_to_details
        # go to next page
        next_button.click()


def get_links_to_issuers(driver) -> list:
    # Get all the links to each issuer from the main page

    links_to_issuers = []
    while True:
        # find table on page and add links to each issuer
        table = driver.find_element_by_id('lvIssuers')
        for row in table.find_elements_by_css_selector('tr'):
            for cell in row.find_elements_by_class_name('sorting_1'):
                # this is the blue link part of each table row
                try:
                    link = cell.find_element_by_tag_name(
                        'a').get_attribute('href')
                    links_to_issuers.append(link)
                except NoSuchElementException:
                    pass

        print("link to issuer array size", len(links_to_issuers))
        # find next button
        next_button = driver.find_element_by_class_name('next')

        # Check if we can go to the next page or not
        attributes = next_button.get_attribute('class').split(" ")
        for attr in attributes:
            if attr == "disabled":
                return links_to_issuers
        # go to next page
        next_button.click()


def main():
    driver = webdriver.Firefox(executable_path='.\geckodriver.exe')
    driver.maximize_window()  # maximize so all elements are clickable
    driver.implicitly_wait(0.5)

    # Get website loaded
    driver.get("https://emma.msrb.org/IssuerHomePage/State?state=IL")

    # use selenium to accept terms and agreement
    accept_terms(driver)

    links_to_issuers = get_links_to_issuers(driver)
    print("issuers", links_to_issuers)

    # Go to each issuer's securities table    
    links_to_details = []
    for l in links_to_issuers:
        driver.get(l)
        detail_links = get_links_to_issuer_homepage_details(driver)
        links_to_details.extend(detail_links)
    
    print("details", links_to_details)

if __name__ == "__main__":
    main()
